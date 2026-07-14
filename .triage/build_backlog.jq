def score:
  (if .type=="security" then 100 else 0 end)
  + (if .action=="fix-pr" then 30 else 0 end)
  + (if .action=="reply-close" then 20 else 0 end)
  + (if .difficulty=="trivial" then 15 elif .difficulty=="small" then 12 elif .difficulty=="medium" then 6 else 0 end)
  + (.confidence*20);
map(. + {score: score})
| sort_by(-.score)
