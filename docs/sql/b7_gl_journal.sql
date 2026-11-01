-- Source: Fraud Audit Data Request and Extraction Pack, section 3 (verbatim)
-- Journal lines (B7). Capture the time the entry was keyed, not just the posting date. In SAP this is the entry date and time on the document header.

SELECT l.line_id, l.je_id, l.posting_date, h.entry_timestamp, l.account_code,
       l.debit, l.credit, h.created_by AS preparer_id, h.approved_by AS approver_id,
       h.manual_flag AS is_manual, l.description, h.document_type, h.reversal_ind
FROM <journal_line_table> l
JOIN <journal_header_table> h ON h.je_id = l.je_id
WHERE h.entry_timestamp >= :start_date AND h.entry_timestamp < :end_date;
