"""Which date counts as the day a statement was submitted.

Only explicit submission dates are used: the finding's own `draft.submission_date`, else the
`submission_date` recorded on its document. Hearing dates and source dates are not submission dates."""
def submission_date(finding, documents):
    return (finding.get("draft") or {}).get("submission_date") or (documents.get(finding.get("document_id")) or {}).get("submission_date")
