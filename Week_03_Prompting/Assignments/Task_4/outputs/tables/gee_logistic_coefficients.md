| term                                                   |   odds_ratio |   or_ci_lo |   or_ci_hi |   p_value |
|:-------------------------------------------------------|-------------:|-----------:|-----------:|----------:|
| Intercept                                              |        6.381 |      4.028 |     10.108 |  2.86e-15 |
| C(prompt_id)[T.Few-Shot]                               |        0.855 |      0.654 |      1.12  |  0.255    |
| C(prompt_id)[T.ICIO]                                   |        1.361 |      0.991 |      1.87  |  0.057    |
| C(solver)[T.GPT-6 Luna]                                |        1.272 |      0.846 |      1.913 |  0.247    |
| C(solver)[T.Gemini 3.8 Flash]                          |        1.578 |      1.131 |      2.203 |  0.007    |
| C(prompt_id)[T.Few-Shot]:C(solver)[T.GPT-6 Luna]       |        0.786 |      0.496 |      1.245 |  0.305    |
| C(prompt_id)[T.ICIO]:C(solver)[T.GPT-6 Luna]           |        0.786 |      0.477 |      1.294 |  0.344    |
| C(prompt_id)[T.Few-Shot]:C(solver)[T.Gemini 3.8 Flash] |        1.268 |      0.907 |      1.773 |  0.165    |
| C(prompt_id)[T.ICIO]:C(solver)[T.Gemini 3.8 Flash]     |        0.797 |      0.551 |      1.151 |  0.226    |
