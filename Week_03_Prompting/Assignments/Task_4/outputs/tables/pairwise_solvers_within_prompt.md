| prompt_id   | measure   | a                | b                | test          |   statistic |   p_value | effect_name   |   effect | detail                           |   p_holm |
|:------------|:----------|:-----------------|:-----------------|:--------------|------------:|----------:|:--------------|---------:|:---------------------------------|---------:|
| CoT         | correct   | Claude Haiku 5.5 | GPT-6 Luna       | McNemar exact |         4   |  0.388    | risk diff     |   -0.026 | a-only=4, b-only=8, OR=0.50      | 0.775    |
| CoT         | correct   | Claude Haiku 5.5 | Gemini 3.8 Flash | McNemar exact |         0   |  0.016    | risk diff     |   -0.045 | a-only=0, b-only=7, OR=0.07      | 0.047    |
| CoT         | correct   | GPT-6 Luna       | Gemini 3.8 Flash | McNemar exact |         2   |  0.453    | risk diff     |   -0.019 | a-only=2, b-only=5, OR=0.40      | 0.775    |
| Few-Shot    | correct   | Claude Haiku 5.5 | GPT-6 Luna       | McNemar exact |         6   |  1        | risk diff     |    0     | a-only=6, b-only=6, OR=1.00      | 1        |
| Few-Shot    | correct   | Claude Haiku 5.5 | Gemini 3.8 Flash | McNemar exact |         0   |  0.000977 | risk diff     |   -0.071 | a-only=0, b-only=11, OR=0.04     | 0.003    |
| Few-Shot    | correct   | GPT-6 Luna       | Gemini 3.8 Flash | McNemar exact |         0   |  0.000977 | risk diff     |   -0.071 | a-only=0, b-only=11, OR=0.04     | 0.003    |
| ICIO        | correct   | Claude Haiku 5.5 | GPT-6 Luna       | McNemar exact |         3   |  1        | risk diff     |    0     | a-only=3, b-only=3, OR=1.00      | 1        |
| ICIO        | correct   | Claude Haiku 5.5 | Gemini 3.8 Flash | McNemar exact |         0   |  0.25     | risk diff     |   -0.019 | a-only=0, b-only=3, OR=0.14      | 0.75     |
| ICIO        | correct   | GPT-6 Luna       | Gemini 3.8 Flash | McNemar exact |         0   |  0.25     | risk diff     |   -0.019 | a-only=0, b-only=3, OR=0.14      | 0.75     |
| CoT         | latency_s | Claude Haiku 5.5 | GPT-6 Luna       | Wilcoxon      |        10   |  4.21e-27 | rank-biserial |   -0.998 | median diff=-7.41, n_nonzero=155 | 1.26e-26 |
| CoT         | latency_s | Claude Haiku 5.5 | Gemini 3.8 Flash | Wilcoxon      |        15   |  4.64e-27 | rank-biserial |   -0.998 | median diff=-6.7, n_nonzero=155  | 1.26e-26 |
| CoT         | latency_s | GPT-6 Luna       | Gemini 3.8 Flash | Wilcoxon      |      3786   |  5.45e-05 | rank-biserial |    0.374 | median diff=0.907, n_nonzero=155 | 5.45e-05 |
| Few-Shot    | latency_s | Claude Haiku 5.5 | GPT-6 Luna       | Wilcoxon      |         3   |  3.68e-27 | rank-biserial |   -1     | median diff=-8.44, n_nonzero=155 | 1.1e-26  |
| Few-Shot    | latency_s | Claude Haiku 5.5 | Gemini 3.8 Flash | Wilcoxon      |         6   |  3.9e-27  | rank-biserial |   -0.999 | median diff=-9.94, n_nonzero=155 | 1.1e-26  |
| Few-Shot    | latency_s | GPT-6 Luna       | Gemini 3.8 Flash | Wilcoxon      |      4620   |  0.011    | rank-biserial |   -0.236 | median diff=-0.61, n_nonzero=155 | 0.011    |
| ICIO        | latency_s | Claude Haiku 5.5 | GPT-6 Luna       | Wilcoxon      |       131   |  4.32e-26 | rank-biserial |   -0.978 | median diff=-9.94, n_nonzero=155 | 8.64e-26 |
| ICIO        | latency_s | Claude Haiku 5.5 | Gemini 3.8 Flash | Wilcoxon      |        12   |  4.38e-27 | rank-biserial |   -0.998 | median diff=-10.9, n_nonzero=155 | 1.31e-26 |
| ICIO        | latency_s | GPT-6 Luna       | Gemini 3.8 Flash | Wilcoxon      |      5356   |  0.218    | rank-biserial |   -0.114 | median diff=-0.24, n_nonzero=155 | 0.218    |
| CoT         | rcaf1     | Claude Haiku 5.5 | GPT-6 Luna       | Wilcoxon      |        34   |  0.397    | rank-biserial |   -0.253 | median diff=0, n_nonzero=13      | 0.397    |
| CoT         | rcaf1     | Claude Haiku 5.5 | Gemini 3.8 Flash | Wilcoxon      |         0   |  0.011    | rank-biserial |   -1     | median diff=0, n_nonzero=7       | 0.034    |
| CoT         | rcaf1     | GPT-6 Luna       | Gemini 3.8 Flash | Wilcoxon      |         8.5 |  0.164    | rank-biserial |   -0.528 | median diff=0, n_nonzero=8       | 0.328    |
| Few-Shot    | rcaf1     | Claude Haiku 5.5 | GPT-6 Luna       | Wilcoxon      |        59.5 |  0.977    | rank-biserial |   -0.008 | median diff=0, n_nonzero=15      | 0.977    |
| Few-Shot    | rcaf1     | Claude Haiku 5.5 | Gemini 3.8 Flash | Wilcoxon      |         1   |  0.002    | rank-biserial |   -0.974 | median diff=0, n_nonzero=12      | 0.005    |
| Few-Shot    | rcaf1     | GPT-6 Luna       | Gemini 3.8 Flash | Wilcoxon      |         1   |  0.002    | rank-biserial |   -0.974 | median diff=0, n_nonzero=12      | 0.005    |
| ICIO        | rcaf1     | Claude Haiku 5.5 | GPT-6 Luna       | Wilcoxon      |        10.5 |  1        | rank-biserial |    0     | median diff=0, n_nonzero=6       | 1        |
| ICIO        | rcaf1     | Claude Haiku 5.5 | Gemini 3.8 Flash | Wilcoxon      |         0   |  0.083    | rank-biserial |   -1     | median diff=0, n_nonzero=3       | 0.25     |
| ICIO        | rcaf1     | GPT-6 Luna       | Gemini 3.8 Flash | Wilcoxon      |         0   |  0.083    | rank-biserial |   -1     | median diff=0, n_nonzero=3       | 0.25     |
