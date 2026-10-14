| prompt_id   | measure   | test      |   statistic |   df |   p_value | effect_name   |   effect |   n_paired |   n_dropped |
|:------------|:----------|:----------|------------:|-----:|----------:|:--------------|---------:|-----------:|------------:|
| CoT         | correct   | Cochran Q |       5.692 |    2 |  0.058    | eta2_Q        |    0.018 |        155 |           0 |
| Few-Shot    | correct   | Cochran Q |      14.235 |    2 |  0.000811 | eta2_Q        |    0.046 |        155 |           0 |
| ICIO        | correct   | Cochran Q |       3     |    2 |  0.223    | eta2_Q        |    0.01  |        155 |           0 |
| CoT         | latency_s | Friedman  |     223.239 |    2 |  3.34e-49 | Kendall W     |    0.72  |        155 |           0 |
| Few-Shot    | latency_s | Friedman  |     226.116 |    2 |  7.93e-50 | Kendall W     |    0.729 |        155 |           0 |
| ICIO        | latency_s | Friedman  |     226.697 |    2 |  5.94e-50 | Kendall W     |    0.731 |        155 |           0 |
| CoT         | rcaf1     | Friedman  |       5.571 |    2 |  0.062    | Kendall W     |    0.018 |        155 |           0 |
| Few-Shot    | rcaf1     | Friedman  |      10.379 |    2 |  0.006    | Kendall W     |    0.033 |        155 |           0 |
| ICIO        | rcaf1     | Friedman  |       3     |    2 |  0.223    | Kendall W     |    0.01  |        155 |           0 |
