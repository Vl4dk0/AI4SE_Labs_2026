| solver      | measure   | a        | b        | test          |   statistic |   p_value | effect_name   |   effect | detail                            |   p_holm |
|:------------|:----------|:---------|:---------|:--------------|------------:|----------:|:--------------|---------:|:----------------------------------|---------:|
| all solvers | correct   | CoT      | Few-Shot | McNemar exact |         7   |  0.093    | risk diff     |    0.019 | a-only=16, b-only=7, OR=2.29      | 0.186    |
| all solvers | correct   | CoT      | ICIO     | McNemar exact |         4   |  0.118    | risk diff     |   -0.015 | a-only=4, b-only=11, OR=0.36      | 0.186    |
| all solvers | correct   | Few-Shot | ICIO     | McNemar exact |         5   |  0.002    | risk diff     |   -0.034 | a-only=5, b-only=21, OR=0.24      | 0.007    |
| all solvers | latency_s | CoT      | Few-Shot | Wilcoxon      |     32074   |  2.5e-14  | rank-biserial |    0.408 | median diff=2.13, n_nonzero=465   | 7.49e-14 |
| all solvers | latency_s | CoT      | ICIO     | Wilcoxon      |     48087   |  0.036    | rank-biserial |    0.112 | median diff=1.02, n_nonzero=465   | 0.036    |
| all solvers | latency_s | Few-Shot | ICIO     | Wilcoxon      |     40582.5 |  2.77e-06 | rank-biserial |   -0.251 | median diff=-0.624, n_nonzero=465 | 5.53e-06 |
| all solvers | rcaf1     | CoT      | Few-Shot | Wilcoxon      |        69.5 |  0.017    | rank-biserial |    0.537 | median diff=0, n_nonzero=24       | 0.034    |
| all solvers | rcaf1     | CoT      | ICIO     | Wilcoxon      |        46   |  0.132    | rank-biserial |   -0.399 | median diff=0, n_nonzero=17       | 0.132    |
| all solvers | rcaf1     | Few-Shot | ICIO     | Wilcoxon      |        70.5 |  0.000931 | rank-biserial |   -0.676 | median diff=0, n_nonzero=29       | 0.003    |
