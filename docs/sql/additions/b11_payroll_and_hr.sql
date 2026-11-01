-- ASSUMPTION: written by Klaus Konsults as a default, not part of the pack.
-- Dataset B11. Payroll and HR, one row per employee per pay run.
-- Column names are provisional defaults (see docs/data_dictionary.md) and the client can override them.
-- Replace table names in angle brackets, verify every mapping with the client's data dictionary,
-- and run with a row count check.

SELECT t.<employee_id> AS employee_id,
       t.<employee_bank_account> AS employee_bank_account,
       t.<hire_date> AS hire_date,
       t.<exit_date> AS exit_date,
       t.<department> AS department,
       t.<pay_run_id> AS pay_run_id,
       t.<pay_date> AS pay_date,
       t.<pay_amount> AS pay_amount,
       t.<attendance_days> AS attendance_days
FROM <payroll_table> t
WHERE t.<pay_date> >= :start_date AND t.<pay_date> < :end_date;
