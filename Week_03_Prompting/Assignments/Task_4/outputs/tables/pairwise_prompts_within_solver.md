| solver           | measure   | a        | b        | test          |   statistic |   p_value | effect_name   |   effect | detail                            |   p_holm |
|:-----------------|:----------|:---------|:---------|:--------------|------------:|----------:|:--------------|---------:|:----------------------------------|---------:|
| Claude Haiku 5.5 | correct   | CoT      | Few-Shot | McNemar exact |         2   |  0.453    | risk diff     |    0.019 | a-only=5, b-only=2, OR=2.50       | 0.453    |
| Claude Haiku 5.5 | correct   | CoT      | ICIO     | McNemar exact |         1   |  0.125    | risk diff     |   -0.032 | a-only=1, b-only=6, OR=0.17       | 0.25     |
| Claude Haiku 5.5 | correct   | Few-Shot | ICIO     | McNemar exact |         1   |  0.021    | risk diff     |   -0.052 | a-only=1, b-only=9, OR=0.11       | 0.064    |
| GPT-6 Luna       | correct   | CoT      | Few-Shot | McNemar exact |         3   |  0.092    | risk diff     |    0.045 | a-only=10, b-only=3, OR=3.33      | 0.185    |
| GPT-6 Luna       | correct   | CoT      | ICIO     | McNemar exact |         2   |  1        | risk diff     |   -0.006 | a-only=2, b-only=3, OR=0.67       | 1        |
| GPT-6 Luna       | correct   | Few-Shot | ICIO     | McNemar exact |         2   |  0.039    | risk diff     |   -0.052 | a-only=2, b-only=10, OR=0.20      | 0.116    |
| Gemini 3.8 Flash | correct   | CoT      | Few-Shot | McNemar exact |         1   |  1        | risk diff     |   -0.006 | a-only=1, b-only=2, OR=0.50       | 1        |
| Gemini 3.8 Flash | correct   | CoT      | ICIO     | McNemar exact |         1   |  1        | risk diff     |   -0.006 | a-only=1, b-only=2, OR=0.50       | 1        |
| Gemini 3.8 Flash | correct   | Few-Shot | ICIO     | McNemar exact |         2   |  1        | risk diff     |    0     | a-only=2, b-only=2, OR=1.00       | 1        |
| Claude Haiku 5.5 | latency_s | CoT      | Few-Shot | Wilcoxon      |       394.5 |  5.84e-24 | rank-biserial |    0.935 | median diff=2.77, n_nonzero=155   | 1.75e-23 |
| Claude Haiku 5.5 | latency_s | CoT      | ICIO     | Wilcoxon      |       422   |  9.63e-24 | rank-biserial |    0.93  | median diff=2.72, n_nonzero=155   | 1.93e-23 |
| Claude Haiku 5.5 | latency_s | Few-Shot | ICIO     | Wilcoxon      |      5504.5 |  0.334    | rank-biserial |   -0.089 | median diff=-0.132, n_nonzero=155 | 0.334    |
| GPT-6 Luna       | latency_s | CoT      | Few-Shot | Wilcoxon      |      3399   |  2.28e-06 | rank-biserial |    0.438 | median diff=1.97, n_nonzero=155   | 6.84e-06 |
| GPT-6 Luna       | latency_s | CoT      | ICIO     | Wilcoxon      |      5670   |  0.503    | rank-biserial |   -0.062 | median diff=-0.314, n_nonzero=155 | 0.503    |
| GPT-6 Luna       | latency_s | Few-Shot | ICIO     | Wilcoxon      |      3772   |  4.89e-05 | rank-biserial |   -0.376 | median diff=-1.35, n_nonzero=155  | 9.79e-05 |
| Gemini 3.8 Flash | latency_s | CoT      | Few-Shot | Wilcoxon      |      5480   |  0.313    | rank-biserial |   -0.093 | median diff=-0.122, n_nonzero=155 | 0.313    |
| Gemini 3.8 Flash | latency_s | CoT      | ICIO     | Wilcoxon      |      3696   |  2.71e-05 | rank-biserial |   -0.389 | median diff=-1.28, n_nonzero=155  | 8.13e-05 |
| Gemini 3.8 Flash | latency_s | Few-Shot | ICIO     | Wilcoxon      |      4712   |  0.017    | rank-biserial |   -0.221 | median diff=-1.2, n_nonzero=155   | 0.034    |
| Claude Haiku 5.5 | rcaf1     | CoT      | Few-Shot | Wilcoxon      |         9   |  0.196    | rank-biserial |    0.5   | median diff=0, n_nonzero=8        | 0.196    |
| Claude Haiku 5.5 | rcaf1     | CoT      | ICIO     | Wilcoxon      |         6   |  0.085    | rank-biserial |   -0.667 | median diff=0, n_nonzero=8        | 0.17     |
| Claude Haiku 5.5 | rcaf1     | Few-Shot | ICIO     | Wilcoxon      |         9.5 |  0.017    | rank-biserial |   -0.756 | median diff=0, n_nonzero=12       | 0.05     |
| GPT-6 Luna       | rcaf1     | CoT      | Few-Shot | Wilcoxon      |        19   |  0.051    | rank-biserial |    0.582 | median diff=0, n_nonzero=13       | 0.102    |
| GPT-6 Luna       | rcaf1     | CoT      | ICIO     | Wilcoxon      |         6   |  0.655    | rank-biserial |   -0.2   | median diff=0, n_nonzero=5        | 0.655    |
| GPT-6 Luna       | rcaf1     | Few-Shot | ICIO     | Wilcoxon      |        10   |  0.017    | rank-biserial |   -0.744 | median diff=0, n_nonzero=12       | 0.051    |
| Gemini 3.8 Flash | rcaf1     | CoT      | Few-Shot | Wilcoxon      |         3   |  1        | rank-biserial |    0     | median diff=0, n_nonzero=3        | 1        |
| Gemini 3.8 Flash | rcaf1     | CoT      | ICIO     | Wilcoxon      |         3.5 |  0.581    | rank-biserial |   -0.3   | median diff=0, n_nonzero=4        | 1        |
| Gemini 3.8 Flash | rcaf1     | Few-Shot | ICIO     | Wilcoxon      |         6   |  0.68     | rank-biserial |   -0.2   | median diff=0, n_nonzero=5        | 1        |
