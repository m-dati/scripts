 select id,user_id,event_data,t_created from audit_events where event='iso_cancel' and t_created > '2018-02-08'::date and event_data like '%aarch64%' order by 4 desc;