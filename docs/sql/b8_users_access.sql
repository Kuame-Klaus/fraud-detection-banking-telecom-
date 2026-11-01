-- Source: Fraud Audit Data Request and Extraction Pack, section 3 (verbatim)
-- Access and role changes (B8)

SELECT u.user_id, u.status AS is_active, r.role_name AS role, p.permission,
       u.last_login, c.change_time, c.changed_by, c.change_type
FROM <user_table> u
LEFT JOIN <user_role_table> r ON r.user_id = u.user_id
LEFT JOIN <role_permission_table> p ON p.role_name = r.role_name
LEFT JOIN <access_change_log> c ON c.user_id = u.user_id
  AND c.change_time >= :start_date;
