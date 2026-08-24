async def get_subject_metrics(self, subject_id: str, subject_end_date: str='') -> Dict[str, Any]:
        """
        Run all subject-level analytics queries for a given subject_id and return
        a single dictionary of metrics.

        Assumes:
        - self.client is an async ClickHouse client
        - await self.client.query(sql, settings={...}) returns an object with
            .column_names and .result_rows (e.g. clickhouse-connect async client)
        """
        if self.client is None:
            await self.connect()

        #print("subject_end_date =", subject_end_date)

        use_subject_end_date = False

        if subject_end_date:
            try:
                datetime.fromisoformat(subject_end_date.replace("Z", "+00:00"))
                use_subject_end_date = True
            except ValueError:
                use_subject_end_date = False

        subject_to_date_expr = (
        f"toDateTime('{subject_end_date}')"
        if use_subject_end_date
        else "mslv.to_date"
        )
    
        subject_to_date_select = (
            f"toDateTime('{subject_end_date}')"
            if use_subject_end_date
            else "to_date"
        )
    
        subject_to_date_max = (
            f"toDateTime('{subject_end_date}')"
            if use_subject_end_date
            else "max(to_date)"
        )

        async def run_query(sql: str) -> List[Dict[str, Any]]:
            """
            Helper: execute a query with a fresh session_id and return a list of row dicts.
            """
            session_id = str(uuid.uuid4())
            response = await self.client.query(sql, settings={'session_id': session_id})

            # clickhouse-connect style; tweak here if your client is different
            rows = getattr(response, 'result_rows', response)
            column_names = getattr(response, 'column_names', [])
            return [dict(zip(column_names, row)) for row in rows]

        metrics: Dict[str, Any] = {}
        metrics["end_date"] = subject_end_date
        
        # 1) tweet_cnt, duration, peak_intensity, time_to_peak
        q1 = f"""
        WITH
            hourly_stats AS (
                SELECT
                    subject_id,
                    toStartOfHour(mc.gregorian_date) AS hour,
                    sum(cnt_messages) AS msgs_per_hour,
                    min(from_date) AS subject_from_date,
                    {subject_to_date_max} AS subject_to_date
                FROM OLAP_Twitter.mvw_cube AS mc
                INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                    ON mc.subject_id = mslv.subject_id
                AND mc.subject_version = mslv.subject_version
                WHERE subject_id = '{subject_id}'
                and mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                GROUP BY subject_id, hour
            ),
            peak_hour AS (
                SELECT
                    subject_id,
                    argMax(hour, msgs_per_hour) AS peak_time,
                    max(msgs_per_hour) AS peak_intensity
                FROM hourly_stats
                GROUP BY subject_id
            ),
            subject_stats AS (
                SELECT
                    subject_id,
                    sum(msgs_per_hour) AS tweet_cnt,
                    min(subject_from_date) AS subject_from_date,
                    max(subject_to_date) AS subject_to_date
                FROM hourly_stats
                GROUP BY subject_id
            )
        SELECT
            tweet_cnt as tweet_count,
            dateDiff('hour', s.subject_from_date, s.subject_to_date) AS duration_hours,
            p.peak_intensity,
            dateDiff('hour', s.subject_from_date, p.peak_time) AS time_to_peak_hours
        FROM subject_stats s
        JOIN peak_hour p USING (subject_id)
        """

        rows = await run_query(q1)
        if rows:
            metrics.update(rows[0])

        # 2) average growth rate
        q2 = f"""
        SELECT avg(growth_per_hour) AS average_growth_rate
        FROM
        (
            SELECT
                subject_id,
                hour,
                value,
                value - lagInFrame(value) OVER w AS growth_per_hour
            FROM
            (
                SELECT
                    subject_id,
                    gregorian_date AS hour,
                    sum(cnt_messages) AS value
                FROM OLAP_Twitter.mvw_cube mc 
                INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                    ON mc.subject_id = mslv.subject_id
                AND mc.subject_version = mslv.subject_version
                AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                WHERE subject_id = '{subject_id}'
                GROUP BY subject_id, hour
            )
            WINDOW w AS
            (
                PARTITION BY subject_id
                ORDER BY hour
                ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
            )
            ORDER BY subject_id, hour
        )
        """
        rows = await run_query(q2)
        if rows:
            metrics.update(rows[0])  # {"avg_growth_rate": ...}

        # 3) half-life in hours after peak until activity drops below half of peak_intensity
        q3 = f"""
        WITH
            hourly_stats AS (
                SELECT
                    subject_id,
                    toStartOfHour(mc.gregorian_date) AS hour,
                    sum(cnt_messages) AS msgs_per_hour
                FROM OLAP_Twitter.mvw_cube AS mc
                INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                    ON mc.subject_id = mslv.subject_id
                AND mc.subject_version = mslv.subject_version
                AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                WHERE subject_id = '{subject_id}'
                GROUP BY subject_id, hour
            ),
            peak_hour AS (
                SELECT
                    subject_id,
                    argMax(hour, msgs_per_hour) AS peak_time,
                    max(msgs_per_hour) AS peak_intensity
                FROM hourly_stats
                GROUP BY subject_id
            ),
            half_life_hour AS (
                SELECT
                    h.subject_id,
                    min(h.hour) AS half_life_time
                FROM hourly_stats h
                JOIN peak_hour p USING (subject_id)
                WHERE
                    h.hour > p.peak_time
                    AND h.msgs_per_hour <= p.peak_intensity / 2
                GROUP BY h.subject_id
            )
        SELECT
            dateDiff('hour', p.peak_time, hl.half_life_time) AS half_life_hours
        FROM peak_hour p
        JOIN half_life_hour hl USING (subject_id)
        """
        rows = await run_query(q3)
        if rows:
            metrics.update(rows[0])  # {"half_life": ...}

        # 4) engagement & spread metrics
        q4 = f"""
        SELECT
            sum(spread) AS impressions_total,
            sum(cnt_retweet_on_post + cnt_quote_on_post) AS rt_qt, 
            sum(mulv.cnt_followers) * sum(spread) AS weighted_impression_propagation,
            sum(cnt_retweet_on_post + cnt_reply_on_post + cnt_quote_on_post + cnt_like_on_post) AS engagements_total,
            2 * engagements_total / countDistinct(mc.user_id) * (countDistinct(mc.user_id) - 1) AS network_density,
            IF(sum(spread) = 0, 0, engagements_total / sum(spread)) * 100 AS engagement_rate,
            IF(sum(spread) = 0, 0, rt_qt / sum(spread)) * 100 AS virality_rate,
            sumIf(cnt_messages, mulv.cnt_followers > 10000) / sum(cnt_messages) AS influencer_share_of_voice,
            sumIf(cnt_messages, mulv.cnt_followers < 10000) / sum(cnt_messages) AS ordinary_user_participation_ratio,
            sumIf(cnt_messages, sentiment_aspect = 'negative') / sum(cnt_messages) AS negative_ratio,
            sumIf(cnt_messages, sentiment_aspect = 'positive') / sum(cnt_messages) AS positive_ratio,
            sumIf(cnt_messages, sentiment_aspect = 'neutral')  / sum(cnt_messages) AS neutral_ratio
        FROM OLAP_Twitter.mvw_cube mc 
        INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id
        LEFT JOIN OLAP_Twitter.mvw_user_last_version mulv FINAL
            ON mc.user_id = mulv.user_id
        WHERE mc.subject_id = '{subject_id}'
        AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
        """
        rows = await run_query(q4)
        if rows:
            metrics.update(rows[0])

        # 5) sentiment distribution & emotional per sentiment (multi-row)
        q5 = f"""
            WITH 
                (
                    SELECT count(*) 
                    FROM 
                    (
                        SELECT arrayJoin(
                            multiIf(length(sentiment_public) = 0, ['neu'], sentiment_public)
                        ) AS sentiment
                        FROM OLAP_Twitter.mvw_cube mc 
                        INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id 
                            AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                        WHERE mc.subject_id = '{subject_id}'
                    )
                ) AS total_cnt
            select sum(log_em) / log(7) as emotional_diversity
            from 
            (
                SELECT 
                    sentiment, 
                    count(*) AS cnt, 
                    round(count(*) / total_cnt, 4) AS share,
                    - share * log(share) as log_em 
                FROM 
                (
                    SELECT 
                        arrayJoin(
                            multiIf(length(sentiment_public) = 0, ['neu'], sentiment_public)
                        ) AS sentiment
                    FROM OLAP_Twitter.mvw_cube mc 
                    INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                        ON mc.subject_id = mslv.subject_id 
                        AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                    WHERE mc.subject_id = '{subject_id}'
                )
                GROUP BY sentiment
                ORDER BY sentiment
            )

        """
        rows = await run_query(q5)
        metrics["emotional_diversity"] = rows[0]  # list of {sentiment_public, ...}

        # 6) emotional diversity (Shannon entropy over sentiments)
        q6 = f"""
            WITH 
                (
                    SELECT count(*) 
                    FROM 
                    (
                        SELECT arrayJoin(
                            multiIf(length(sentiment_public) = 0, ['neu'], sentiment_public)
                        ) AS sentiment
                        FROM OLAP_Twitter.mvw_cube mc 
                        INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id 
                            AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                        WHERE mc.subject_id = '{subject_id}'
                    )
                ) AS total_cnt

            SELECT 
                sentiment, 
                count(*) AS cnt, 
                round(count(*) / total_cnt, 4) AS ratio
            FROM 
            (
                SELECT 
                    arrayJoin(
                        multiIf(length(sentiment_public) = 0, ['neu'], sentiment_public)
                    ) AS sentiment
                FROM OLAP_Twitter.mvw_cube mc 
                INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                    ON mc.subject_id = mslv.subject_id 
                    AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                WHERE mc.subject_id = '{subject_id}'
            )
            GROUP BY sentiment
            ORDER BY sentiment

        """
        rows = await run_query(q6)
        if rows:
            metrics["sentiment_stats"] = rows  # {"emotional_diversity": ...}

        # 7) user count and IW per user (single-row)
        q7 = f"""
        select  max(total_rows) as user_count, 
                SumIf(sum_rt,rn<ABS(CAST(total_rows * 2 / 100 AS UInt64))) / Sum(sum_rt) as network_power_concentration, 
                avg(follower_count) as influencer_weight
        from 
        (
            select mc.user_id, sum(mc.cnt_retweet_on_post) sum_rt, 
                    row_number() over (order by sum_rt desc) as rn,
                    COUNT(*) OVER () AS total_rows,
                    max(mulv.cnt_followers) as follower_count
            from OLAP_Twitter.mvw_cube mc 
            INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id
            left join OLAP_Twitter.mvw_user_last_version mulv final
            on mc.user_id = mulv.user_id
            WHERE mc.subject_id = '{subject_id}'
            AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
            group by mc.user_id
        )
        """
        rows = await run_query(q7)
        metrics["user_stats"] = rows  # list of per-user aggregates

        # 8) Flow-tag activity & user entropy
        q8 = f"""
        WITH
            (
                SELECT sum(cnt_messages) AS total_messages
                FROM OLAP_Twitter.mvw_cube mc
                INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id
                LEFT JOIN OLAP_Twitter.mvw_user_last_version mulv FINAL
                    ON mc.user_id = mulv.user_id
                LEFT ARRAY JOIN Flow AS flow_tag
                WHERE mc.subject_id = '{subject_id}'
                AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
            ) AS total_message,
            (
                SELECT countDistinct(mc.user_id) AS total_users
                FROM OLAP_Twitter.mvw_cube mc
                INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id
                LEFT JOIN OLAP_Twitter.mvw_user_last_version mulv FINAL
                    ON mc.user_id = mulv.user_id
                LEFT ARRAY JOIN Flow AS flow_tag
                WHERE mc.subject_id = '{subject_id}'
                AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
            ) AS total_users,
            per_tag AS (
                SELECT
                    flow_tag,
                    sum(cnt_messages) AS msg_count,
                    sum(cnt_messages) / total_message AS p_activity,
                    -sum(cnt_messages) / total_message * log2(sum(cnt_messages) / total_message) AS entropy_contrib_activity,
                    countDistinct(mc.user_id) AS user_count,
                    countDistinct(mc.user_id) / total_users AS p_unweighted,
                    -countDistinct(mc.user_id) / total_users * log2(countDistinct(mc.user_id) / total_users) AS entropy_contrib_unweighted
                FROM OLAP_Twitter.mvw_cube mc
                INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id
                LEFT JOIN OLAP_Twitter.mvw_user_last_version mulv FINAL
                    ON mc.user_id = mulv.user_id
                LEFT ARRAY JOIN Flow AS flow_tag
                WHERE mc.subject_id = '{subject_id}'
                AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                GROUP BY flow_tag
            )
        SELECT
            sum(entropy_contrib_activity) AS H_activity, 
            exp(sum(entropy_contrib_activity)) AS d1_activity,
            1 / sum(p_activity * p_activity) AS d2_activity,
            sum(entropy_contrib_unweighted) AS H_unweighted, 
            exp(sum(entropy_contrib_unweighted)) AS d1_unweighted,
            1 / sum(p_unweighted * p_unweighted) AS d2_unweighted
        FROM per_tag
        """
        rows = await run_query(q8)
        if rows:
            metrics.update(rows[0])

        # 9) Flow-tag entropy weighted by followers
        q9 = f"""
        WITH
            (
                SELECT sum(cnt_followers) AS followers
                FROM 
                (
                    SELECT user_id
                    FROM OLAP_Twitter.mvw_cube mc
                    INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id
                    WHERE mc.subject_id = '{subject_id}'
                    AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                    GROUP BY user_id
                ) a
                LEFT JOIN OLAP_Twitter.mvw_user_last_version mulv FINAL
                    ON a.user_id = mulv.user_id
            ) AS total_followers,
            per_follower AS
            (
                SELECT
                    flow_tag,
                    sum(cnt_followers) / total_followers AS p_influence,
                    -sum(cnt_followers) / total_followers * log2(sum(cnt_followers) / total_followers) AS entropy_contrib_influence
                FROM 
                (
                    SELECT user_id
                    FROM OLAP_Twitter.mvw_cube mc
                    INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id
                    WHERE mc.subject_id = '{subject_id}'
                    AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                    GROUP BY user_id
                ) a
                LEFT JOIN OLAP_Twitter.mvw_user_last_version mulv FINAL
                    ON a.user_id = mulv.user_id
                LEFT ARRAY JOIN Flow AS flow_tag
                GROUP BY flow_tag
            )
        SELECT
            sum(entropy_contrib_influence) AS H_influence, 
            exp(sum(entropy_contrib_influence)) AS d1_influence,
            1 / sum(p_influence * p_influence) AS d2_influence
        FROM per_follower
        """
        rows = await run_query(q9)
        if rows:
            metrics.update(rows[0])

        # 10) average degree in user interaction graph
        q10 = f"""
        SELECT
            (
                SELECT sum(cnt_retweet_by_user + cnt_quote_by_user + cnt_reply_by_user)
                FROM OLAP_Twitter.mvw_cube mc
                INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id
                WHERE subject_id = '{subject_id}'
                AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
            ) / countDistinct(users) AS avrage_degree
        FROM
        (
            SELECT user_id AS users
            FROM OLAP_Twitter.tbl_msgs tm 
            LEFT JOIN OLAP_Base.mvw_subject_last_version AS mslv
                ON tm.subject_id = mslv.subject_id
            WHERE
                msg_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                AND subject_id = '{subject_id}'
            GROUP BY user_id

            UNION ALL 

            SELECT source_user_id AS users
            FROM OLAP_Twitter.tbl_msgs tm 
            LEFT JOIN OLAP_Base.mvw_subject_last_version AS mslv
                ON tm.subject_id = mslv.subject_id
            WHERE
                msg_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                AND subject_id = '{subject_id}'
                AND source_user_id != ''
            GROUP BY source_user_id
        ) a
        """
        rows = await run_query(q10)
        if rows:
            metrics.update(rows[0])  # {"avrage_degree": ...}

        # 11) burstiness index from growth series
        q11 = f"""
        WITH
            time_bounds AS (
                SELECT
                    toStartOfHour(toDateTime64(min(msg_date), 3)) AS start_time,
                    toStartOfHour(toDateTime64(max(msg_date), 3)) AS end_time,
                    dateDiff(
                        'hour',
                        toStartOfHour(toDateTime64(min(msg_date), 3)),
                        toStartOfHour(toDateTime64(max(msg_date), 3))
                    ) + 1 AS hours_count
                FROM OLAP_Twitter.tbl_msgs tm
                LEFT JOIN OLAP_Base.mvw_subject_last_version AS mslv
                    ON tm.subject_id = mslv.subject_id
                WHERE
                    msg_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                    AND tm.subject_id = '{subject_id}'
            ),
            hourly_series AS (
                SELECT
                    addHours(start_time, h) AS ts
                FROM time_bounds
                ARRAY JOIN range(hours_count) AS h
            ),
            per_hour_counts AS (
                SELECT
                    toStartOfHour(toDateTime64(msg_date, 3)) AS ts,
                    count() AS msgs
                FROM OLAP_Twitter.tbl_msgs tm
                LEFT JOIN OLAP_Base.mvw_subject_last_version AS mslv
                    ON tm.subject_id = mslv.subject_id
                WHERE
                    msg_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                    AND tm.subject_id = '{subject_id}'
                GROUP BY ts
            ),
            full_ts_series AS (
                SELECT
                    hs.ts,
                    coalesce(ph.msgs, 0) AS msgs
                FROM hourly_series hs
                LEFT JOIN per_hour_counts ph USING (ts)
            ),
            growth_series AS (
                SELECT
                    ts,
                    msgs,
                    msgs - lagInFrame(msgs) OVER (
                        ORDER BY ts
                        ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
                    ) AS growth_rate
                FROM full_ts_series
            ),
            result AS 
            (
                SELECT
                    avgIf(growth_rate, growth_rate > 0) AS avg_growth_per_hour,
                    stddevSamp(growth_rate) AS stdev_growth_per_hour
                FROM growth_series
                WHERE growth_rate IS NOT NULL
            )
        SELECT
            abs((stdev_growth_per_hour - avg_growth_per_hour))
                / (stdev_growth_per_hour + avg_growth_per_hour) AS burstiness_index
        FROM result
        """
        rows = await run_query(q11)
        if rows:
            metrics.update(rows[0])  # {"avg_growth_per_hour": ..., "stdev_growth_per_hour": ..., "burstiness_index": ...}

        # 12) acceleration index
        q12 = f"""
            select avg(lag_param) as acceleration_index
            from 
            (
                select subject_id, gregorian_date, cnt_messages, delta_messages, 
                            if(delta_messages - lag(delta_messages, 1) OVER w > 0, delta_messages - lag(delta_messages, 1) OVER w , 0) AS lag_messages,
                            lag_messages / cnt_messages as lag_param
                from 
                (
                    SELECT 
                        subject_id,
                        gregorian_date,
                        cnt_messages,
                        cnt_messages - lag(cnt_messages, 1) OVER w AS delta_messages
                    FROM 
                    (
                        SELECT 
                            mc.subject_id, 
                            mc.gregorian_date, 
                            mc.cnt_messages
                        FROM OLAP_Twitter.mvw_cube mc 
                        INNER JOIN OLAP_Base.mvw_subject_last_version mslv FINAL
                            ON mc.subject_id = mslv.subject_id 
                            AND mc.gregorian_date BETWEEN mslv.from_date AND {subject_to_date_expr}
                        WHERE subject_id = '{subject_id}'
                    ) 
                    WINDOW w AS (PARTITION BY subject_id ORDER BY gregorian_date)
                    ORDER BY gregorian_date
                )
                WINDOW w AS (PARTITION BY subject_id ORDER BY gregorian_date)
                ORDER BY gregorian_date
            )
            """
        rows = await run_query(q12)
        if rows:
            metrics.update(rows[0])  # {"acceleration index"}
        
        q13 = f"""
        select mslv.subject_id as subject_id, mslv.title as subject_title, from_date, {subject_to_date_select} as to_date, 
                category, regions, te_domain.title as domain, te_concept.title as concept,
                te_strategy.title as strategy, te_tactic.title as tactic
        from OLAP_Base.mvw_subject_last_version mslv final
        left join OLAP_Base.tbl_entities as te_domain final
        on te_domain.entities_id=mslv.domains
        left join OLAP_Base.tbl_entities as te_concept final
        on te_concept.entities_id=mslv.concepts
        left join OLAP_Base.tbl_entities as te_strategy final
        on te_strategy.entities_id=mslv.strategies
        left join OLAP_Base.tbl_entities as te_tactic final
        on te_tactic.entities_id=mslv.tactics
        where subject_id = '{subject_id}'
        """
        
        rows = await run_query(q13)
    
        metrics["subject_info"] = rows  # list of per-user aggregates



        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()  # Converts to standard ISO string
                return super().default(obj)

            
        r = json.dumps(metrics, cls=DateTimeEncoder)
        return json.loads(r)
        # print(metrics)
        mapper = Api1ToApi2Mapper()
        mapper = mapper.transform(metrics)
        payload = json.dumps(mapper, default=str)
        
        conn = http.client.HTTPConnection("insightengine.aigpu")
        headers = { 'Content-Type': "application/json" }
        conn.request("POST", "/api/events/interpret", payload, headers)
        res = conn.getresponse()
        data = res.read()
        try:
            if data:
                return json.loads(data)
            else:
                return ""
        except Exception as e:
            return f"error while fetching data: {e}"