| solver           | measure   | test      |   statistic |   df |   p_value | effect_name   |   effect |   n_paired |   n_dropped |
|:-----------------|:----------|:----------|------------:|-----:|----------:|:--------------|---------:|-----------:|------------:|
| Claude Haiku 5.5 | correct   | Cochran Q |       8.167 |    2 |  0.017    | eta2_Q        |    0.026 |        155 |           0 |
| GPT-6 Luna       | correct   | Cochran Q |       7.6   |    2 |  0.022    | eta2_Q        |    0.025 |        155 |           0 |
| Gemini 3.8 Flash | correct   | Cochran Q |       0.4   |    2 |  0.819    | eta2_Q        |    0.001 |        155 |           0 |
| Claude Haiku 5.5 | latency_s | Friedman  |     188.142 |    2 |  1.4e-41  | Kendall W     |    0.607 |        155 |           0 |
| GPT-6 Luna       | latency_s | Friedman  |      29.355 |    2 |  4.22e-07 | Kendall W     |    0.095 |        155 |           0 |
| Gemini 3.8 Flash | latency_s | Friedman  |      14.877 |    2 |  0.000588 | Kendall W     |    0.048 |        155 |           0 |
| Claude Haiku 5.5 | rcaf1     | Friedman  |       7.429 |    2 |  0.024    | Kendall W     |    0.024 |        155 |           0 |
| GPT-6 Luna       | rcaf1     | Friedman  |       7.6   |    2 |  0.022    | Kendall W     |    0.025 |        155 |           0 |
| Gemini 3.8 Flash | rcaf1     | Friedman  |       1     |    2 |  0.607    | Kendall W     |    0.003 |        155 |           0 |
