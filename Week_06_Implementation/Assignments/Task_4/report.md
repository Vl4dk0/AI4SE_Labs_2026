Matching is exact cosine similarity. Stored rows and the query are L2-normalized, so cosine is a dot product. `top_n` takes n rows with `numpy.argpartition`, then sorts those n. That is exact. An index could drop a neighbour, and N is only 828.

One query is O(N d) with d = 768, about 6.4·10^5 multiplies, plus an O(N) partition and a sort of n = 5. Measured mean of `top_n` over 200 calls on the real matrix: 12.6 µs.

`retrieve` embeds the task with the same local model, then calls `top_n`. The query was file, class, method, and docstring for three `missing_code.json` entries.

| query | top 5 (score, kind, qualname) | class header |
| --- | --- | --- |
| OrderStatus.is_terminal | 0.6528 method is_terminal; 0.5786 class_header OrderStatus; 0.5480 test_cancelled_is_terminal; 0.5193 test_shipped_is_terminal; 0.5154 test_reserved_is_not_terminal | yes, rank 2 |
| InventoryLedger.__contains__ | 0.7185 method _require_sku; 0.6807 method __contains__; 0.6751 test_add_stock_unknown_sku; 0.6744 test_available_unknown_sku; 0.6637 test_require_sku_unknown_raises | no |
| Order.__len__ | 0.6867 OrderBuilder.__len__; 0.6444 OrderLog.__len__; 0.6272 Order.__len__; 0.6116 class_header OrderLog; 0.5984 module header | no (OrderLog, not Order) |

The stub method itself is in the top 5 for all three (ranks 1, 2, and 3). The Order query prefers other `__len__` methods. Neighbours that do show up are on the same file and the same idea: terminal-status tests, and SKU checks on the ledger.
