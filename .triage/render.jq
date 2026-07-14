def row: "| #\(.number) | \(.difficulty) | \(.confidence) | \(.area) | \(.title) — _\(.one_liner)_ |";
def table($f): [.[]|select($f)] | (if length==0 then "_none_" else (["| Issue | Diff | Conf | Area | Summary / recommendation |","|---|---|---|---|---|"] + map(row)) | join("\n") end);
.
