---
title: "Simple and Efficient Binomial Protocols for Differential Privacy in MPC"
abbrev: "Binomal DP in MPC"
category: std

docname: draft-case-ppm-binomial-dp-latest
submissiontype: IETF
consensus: true
v: 3
area: "Security"
workgroup: "Privacy Preserving Measurement"
keyword:
 - oneplusoneplusoneplus
 - noise
 - counting coins
venue:
  group: "Privacy Preserving Measurement"
  type: "Working Group"
  mail: "ppm@ietf.org"
  arch: "https://mailarchive.ietf.org/arch/browse/ppm/"
  github: "private-attribution/i-d"
  latest: "https://private-attribution.github.io/i-d/draft-case-ppm-binomial-dp.html"

author:
 -
    name: Benjamin Case
    organization: Meta
    email: bmcase@meta.com
 -
    name: Martin Thomson
    organization: Mozilla
    email: mt@lowentropy.net

normative:

  PRSS:
    title: "High Performance Pseudorandom Secret Sharing (PRSS)"
    date: 2024-07 # TODO(mt)
    seriesinfo:
      Internet-Draft: draft-thomson-ppm-prss-latest
    author:
      -
        name: Martin Thomson
      -
        name: Ben Savage

  MPC-MUL:
    title: "Efficient Protocols for Binary Fields in the 3-Party Honest Majority MPC Setting"
    date: 2024-07 # TODO(mt)
    seriesinfo:
      Internet-Draft: draft-savage-ppm-3phm-mpc-latest
    author:
      -
        name: Ben Savage
      -
        name: Martin Thomson

informative:
  CPSGD:
    title: "cpSGD: Communication-efficient and differentially-private distributed SGD"
    date: 2018-05
    author:
      -
        name: Naman Agarwal
      -
        name: Ananda Theertha Suresh
      -
        name: Felix Yu
      -
        name: Sanjiv Kumar
      -
        name: H. Brendan Mcmahan


--- abstract

A method for computing a binomial noise in Multiparty Computation (MPC) is
described.  The binomial mechanism for differential privacy (DP) is a simple
mechanism that is well suited to MPC, where computation of more complex
algorithms can be expensive.  This document describes how to select the correct
parameters and apply binomial noise in MPC.


--- middle

# Introduction

Using Multiparty Computation (MPC) to compute aggregate statistics has some very
promising privacy characteristics. MPC provides strong assurances about the
confidentiality of input values, relying only on the assumption that the parties
performing the computation do not collude. Depending on the MPC system in use,
the cryptographic assumptions involved can be conservative.  For instance, MPC
is the basis of the Verifiable, Distributed Aggregation Functions (VDAFs)
{{?VDAF=I-D.irtf-cfrg-vdaf}} used in DAP {{?DAP=I-D.ietf-ppm-dap}}.

Depending on how the system is used, particularly for systems where the MPC
system offers some flexibility in how it can be queried, concrete privacy
guarantees are harder to provide.  Multiple aggregations over similar input data
might be computed, leading to aggregates that can be compared to reveal
aggregates over a small set of inputs or even the value of specific inputs.

Differential privacy (DP) {{?DWORK=DOI.10.1561/0400000042}}) offers a framework
for both analyzing and protecting privacy that can be applied to this problem to
great effect.  By adding some amount of noise to aggregates, strong guarantees
can be made about the amount of privacy loss that applies to any given input.

There are multiple methods for applying noise to aggregates, but the one that
offers the lowest amount of noise — and therefore the most useful outputs — is
one where a single entity samples and adds noise, known as central
DP. Alternatives include local DP, where noise is added to each input to
the aggregation, or shuffle DP, which reduces noise requirements for local DP by
shuffling inputs.

Applying noise in a single place ensures that the amount of noise is directly
proportional to the sensitivity (that is, the maximum amount that any input
might contribute to the output) rather than being in some way proportional to
the number of inputs.  The amount of noise relative to aggregates decreases as
the number of inputs increases, meaning that central DP effectively provides an
optimal amount of noise.


## DP Noise in MPC

There are several approaches to adding noise in MPC.

Use of local or shuffle DP is possible. As noted, these methods can add more
noise than is ideal.

Noise can be added by each party independently. Each party adds noise in a
fraction that is based on its understanding of the number of honest parties
present. In two-party MPC, each party has to assume the other is dishonest, so
each adds the entire noise quantity, ultimately doubling the overall noise that
is added. In a three-party honest majority MPC, each party can add half of the
required noise on the assumption that one other party is honest, resulting in a
50% increase in the amount of noise relative to the ideal.

Finally, an MPC protocol can be executed to add noise. The primary drawback of
this approach is that there is an increased cost to generating the noise in MPC.
However, MPC protocols can avoid having to include additional noise in order to
compensate for the risk of information leakage from a dishonest participant.
Adding noise using MPC provides strong assurances that noise is not known to any
party, including the parties that perform the computation, up to the limits of
the MPC scheme in use.  Finally, the costs of computation in MPC scale only with
the privacy parameters for the differential privacy, not the number of inputs.
Amortizing this cost over large sets of inputs can make the additional cost
small.


## Binomal Noise

The Bernoulli distribution provides approximate differential privacy (DP)
{{?DWORK}}. This is sometimes named (epsilon, delta)-differential privacy or (ε,
δ)-differential privacy.  The epsilon value in approximate DP bounds privacy
loss for most contributions to the output, however the delta value is a non-zero
bound on the probability that a higher privacy loss occurs.

A binomial, `Bin(N, p)`, distribution is the number of successes out of `N`
Bernoulli trials, where each Bernoulli trial is a coin flip with success
probability `p`.

Due to the central limit theorem, a binomial distribution with large `N` is a
close approximation of a Normal or Gaussian distribution, which has a number of
useful properties.

This document describes a simple MPC protocol, with several instantiations, for
efficiently computing binomial noise.


## Requirements Language

{::boilerplate bcp14-tagged-bcp}


# The Binomial Mechanism for MPC

The binomial mechanism for DP generates binomial noise in MPC and adds it to
outputs before they are released.

Our parameter choices rely on an analysis from {{CPSGD}}, which provides more
comprehensive formulae for a range of parameters.


To sample from a `Bin(N, p)` distribution in MPC, two things are needed:

* A protocol for Bernoulli trials, or coin-flipping protocol, that produces a
  value of 1 with probability `p` and 0 otherwise.

* A means to sum the value of `N` trials.

This protocol sets `p` to 0.5. This value of `p` provides both an optimal
privacy/utility trade off and good efficiency for computation in MPC. Each
Bernoulli sample requires a single, uniformly distributed bit, which can be done
very efficiently. Using `p = 0.5` also requires the fewest samples for any set
of parameters, except for cases with extremely low variance requirements, which
we consider to be out of scope; see Section 2 of {{CPSGD}}.

There are several ways to instantiate a coin flipping protocol in MPC depending
what MPC protocol is being used.  {{protocols}} describes some basic protocol
instantiations.

For any given set of privacy parameters (epsilon, delta) and for a known
sensitivity, {{compute-n}} describes how to determine the number of Bernoulli
samples needed.

To count the number of successes across these `N` trials, the MPC helpers simply
add the secret shared results of the `N` Bernoulli trials, each or which is
either 0 or 1.  The result of this sum is a sample from a `Bin(N, p)`
distribution. This binomial noise value is then added to the output inside the
MPC and then the final noised result revealed to the appropriate output parties.
That is, if the MPC computes `f(D)`, it outputs shares of the result `f(D) +
Bin(N,p)`.

The party receiving the output can then postprocess this output to get an
unbiased estimate for `f(D)` by subtracting the mean of the `Bin(N,p)`
distribution, which is `N\*p`.

## Document Organization

In the remainder of this document is organized as follows:

* {{scale}} introduces an additional quantization scaling parameter that can
  be used to optimize the privacy/utility tradeoff.

* {{compute-n}} details the process of determining for a given function `f()`
  and privacy parameters how to determine the optimal number of trials, `N`.

* {{protocols}} describes some instantiations of the coin flipping protocol and
  the aggregation protocol.

* {{cost}} includes a cost analysis of different instantiations in both
  computation and communication costs.

* {{comparison}} compares the binomial mechanism to other DP approaches that
  might be used in MPC.

<!-- TODO: overview of some use cases where this approach would be beneficial to use. -->


# Quantization Scale {#scale}


{{CPSGD}} provides an additional "quantization scale" parameter, `s`, for the
binomial mechanism that can be tuned to make it more closely approximate the
Gaussian mechanism and get an improved privacy/utility tradeoff.

The paper defines the application of the binomial mechanism as:

~~~ pseudocode
f(D) + (X - Np) * s
~~~

where `f(D)` is the value that is protected and `X` is a sample from a `Bin(N,
p)` distribution.  This produces a scaled and unbiased output.

The value of `s` is typically smaller than one, meaning that the sample noise is
effectively able to produce non-integer values. However, operating on
non-integer values in MPC is more complex, so this documents uses a modified
version where the MPC computes:

~~~ pseudocode
o = f(D) / s + X
~~~

For an MPC system, the output of the system is shares of this scaled and biased
value. The recipient can reconstruct the an unbiased, unscaled, noised value by:

* Adding the shares it receives: `o = sum(o_1, o_2, …)`
* Correcting for bias: `o - N\*p`
* Scaling the value: `f′(D) = s * (o - N\*p)`

The resulting value is always within `N\*p\*s` of the computed aggregate, but it
could be negative if that aggregate is smaller than `N\*p\*s`.


## Determining number of Bernoulli trials {#compute-n}

Applying noise for differential privacy requires understanding the function
being computed, `f()`, and the private dataset, `D`.  For an `f` that is a
`d`-dimensional query with integer outputs, the output vector is in `ℤ<sup>d</sup>`.  That
is, the output is a `d`-dimensional vector of natural numbers.

The binomial mechanism requires understanding the sensitivity of the result
under three separate norms.

### Sensitivity

Differential privacy describes sensitivity in terms of databases.  In this,
databases are considering "neighboring" if the additional, removal, or sometimes
the substitution of inputs related to a single subject turns one database into
the other.

For two neighboring databases `D_1`, `D_2`, the sensitivity of `f` is:

~~~ pseudocode
||f(D_1) - f(D_2)||<sub>p</sub>
~~~

For `f(D)` that produces output that is a `d`-dimensional vector of integer
values, the `p`-norms of interest for use with the binomial mechanism is the L1,
L2, and L∞ (or Linfty) norms.

The L1 norm of `x` (where x∊ℤ<sup>d</sup>) is:

~~~ pseudocode
sensitivity\_1 = ||x||<sub>1</sub> = sum(i=1..d, |x_i|)
~~~

The L2 norm is:

~~~ pseudocode
sensitivity\_2 = ||x||<sub>2</sub> = sqrt(sum(i=1..d,x_i^2))
~~~

Finally, the L∞ norm is:

~~~ pseudocode
sensitivity\_infty = ||x||∞ = max_i(|x_i|)
~~~

These properties of the function `f()` are all specific to the use case and need
to be known.


## Epsilon and Delta Constraints

The privacy parameters for approximate DP are epsilon, ε, and delta, δ.  These
parameters determine the bounds on privacy loss.

Epsilon may vary considerably, though is typically in the range `[0.01,
10]`. Often, multiple queries spend proportions of a larger epsilon privacy
budget.  For example, a privacy budget of `epsilon=3` might be spent in three
separate queries with epsilon 1 or as four queries with epsilon of 2, 0.1, 0.3,
and 0.6.

Delta is often be fixed in the range
(2<sup>-29</sup>..2<sup>-24</sup>). Typically, the only constraint on delta is
to ensure that `1/delta > population`; that is, expected number of contributions
that will suffer privacy loss greater than epsilon is kept less than one.  For
MPC functions that include very large numbers of inputs, delta might need to be
reduced.

Theorem 1 of {{CPSGD}} gives a way to determine the fewest Bernoulli trials,
`N`, needed to achieve approximate DP.  There are two main constraints that need
to be satisfied which we call the `delta_constraint` and
`epsilon_delta_constraint`.

As the number Bernoulli trials increases, each constraint monotonically allows
for smaller epsilon and delta values to be achieved.  To find the smallest
number of Bernoullis that simultaneously satisfies both constraints, find the
minimum `N` determined by the `delta_constraint` and the minimum `N` determined
by the `epsilon_delta_contraint` and then take the maximum of these two values.

A possible approach to satisfying both constraints is to perform a binary search
over `N` to find the smallest one satisfying both constraints simultaneously.  A
search might be acceptable as the computation only needs to be performed once
for each set of parameters.  An alternative and more direct approach is
described in the following sections.


### Bounding `N` by `delta_constraint`

The `delta_constraint` is a function of delta, the dimension, `d`, the
`sensitivity\_infty`, the quantization scale, `s`, and `p` (which is fixed to 0.5
in this document).  This produces a simple formula for determining the minimum
value of `N`:

~~~ pseudocode
N >= 4\*max(23\*ln(10\*d/delta), 2\*sensitivity\_infty/s)
~~~


### Bounding `N` by `epsilon_delta_constraint`

The `epsilon_delta_constraint` is a function of epsilon, delta, `s`, `d`,
`sensitivity\_1`, `sensitivity\_2`, `sensitivity\_infty`, and `p` (0.5).  It is a
more complicated formula.


For the `epsilon_delta_constraint`, {{CPSGD}} defines some intermediate
functions of the success probability, `p`. For `p = 0.5`, these become fixed
constants:

~~~ pseudocode
b_p = 1/3
c_p = sqrt(2)\*7/4
d_p = 2/3
~~~

The `epsilon_delta_constraint`, as written in formula (7) of {{CPSGD}},
determines what epsilon is currently attained by the provided `N` and other
parameters:

~~~ pseudocode
epsilon =
  sensitivity\_2\*sqrt(2\*ln(1.25/delta))
    / (s/2\*sqrt(N))
  + (sensitivity\_2\*c_p\*sqrt(ln(10/delta)) + sensitivity\_1\*b_p)
    / ((s/4)\*(1-delta/10) \* N)
  + (2/3\*sensitivity\_infty\*ln(1.25/delta)
      + sensitivity\_infty\*d_p\*ln(20\*d/delta)\*ln(10/delta))
    / ((s/4)\*N)
~~~

The value of `N` for a fixed set of values for epsilon, delta, sensitivity, and
`s`, is a quadratic equation in `N`.

To see this first write equation (7) as with other variables gathered into
constants `c_1` and `c_2`:

~~~ pseudocode
epsilon = c_1 / sqrt(N) + c_2 / N
c_1 = 2\*sensitivity\_2\*sqrt(2\*ln(1.25/delta))
c_2 = 4 / s\*(
    (sensitivity\_2\*c_p\*sqrt(ln(10/delta)) + sensitivity\_1\*b_p)
      / (1-delta/10)
    + 2\*sensitivity\_infty\*ln(1.25/delta) / 3
    + sensitivity\_infty\*d_p\*ln(20\*d/delta)\*ln(10/delta)
  )
~~~

The formula for epsilon can then be written as a quadratic equation in `N`:

~~~ pseudocode
0 = (epsilon / c_1)^2\*N^2 + (2\*epsilon\*c_2 / c_1^2 - 1)\*N + (c_2 / c_1)^2
~~~

Once the values of all the other parameters are fixed, this can be solved with
the quadratic formula.


### Setting the Quantization Scale

Setting the quantization scale correctly can help get the best privacy/utility
trade offs for the mechanism.  An additional equation to note is the error of
the mechanism which we would like to minimize subject to the privacy constraints

~~~ pseudocode
error = d\*s^2\*N\*p\*(1-p) = 0.25\*d\*s^2\*N
~~~

{{CPSGD}} discusses more about why 0.5 is the optimal choice for `p`.  When it
comes to setting the quantization scale s, making it smaller will decrease the
error directly but also require a larger `N`.

It is generally the case that making `s` smaller will continually decrease the
error, but at some point there is necessarily a performance constraint from the
MPC cost of how large an `N` is practical.

One approach to setting the scale parameter would be to first determine an upper
bound allowed for `N` and then set `s` as small as possible within that
constraint.  Another approach would be to look for a point at which decreasing
`s` and increasing `N` leads to diminishing returns in reducing the error of the
mechanism.


# Noise Generation Algorithm

Once the optimal number of Bernoulli trials has been determined, there are two
phases to the algorithm:

1. Perform a distributed coin flipping protocol so that all helpers hold secret
   shares of 0 or 1 with probability, `p`.

2. Sum up these secret shared samples into a sample from a `Bin(N, p)`.

This document uses `p = 0.5`, so the coin flipping protocol can use a
uniformly-distributed source of entropy.


## Coin Flipping and Aggregation Protocols {#protocols}

The use of the binomial mechanism for `p = 0.5` in a concrete MPC requires a
protocol for jointly computing a number of random bits. Different systems will
have different requirements. This section describes three basic protocols that
can be used to compute the binomial distribution.


### Three Party Honest Majority

A three party honest majority system is appealing because there are very
efficient protocols for performing multiplication; see {{MPC-MUL}}.

Two protocols are described:

* A binary circuit allows the coin flip to be performed without any
  communication cost using PRSS {{PRSS}}. Aggregation requires the use of an
  addition circuit, which requires one binary multiplication per bit.

* A circuit using prime fields allows the aggregation to be performed without
  communication, but the coin flip protocol, which also uses PRSS, requires a
  modulus conversion operation.

Overall, the binary circuit is more efficient in terms of communication costs,
but it might be easier to integrate the prime field circuit into a system that
uses prime fields.


### Three Party Binary Field Protocol

A coin flip protocol in a three party honest majority system simply samples a
random share using PRSS.  The result is a three-way, replicated sharing of a
random binary value.

Aggregating these values can be performed using a binary circuit in a tree.  Two
bits, `a` and `b`, are added to form a binary value, `{a∧b, a⊕b}`.

This process is continued pairwise. The resulting pairs, `{a1, a2}` and `{b1,
b2}`, are also added pairwise to produce a three-bit value, `{a1∧b1,
a1⊕b1⊕(a2∧b2), a2⊕b2}`.

Each successive iteration involves one more bit and half as many values, until a
single value with `log_2(N)` bits is produced.

This aggregation process requires at most `4N` binary multiplications.


### Three Party Large Prime Field Protocol

Addition of values in a prime field with a modulus greater than the number of
samples (N) can be performed trivially. However, producing a replicated secret
sharing across three parties using a single bit sample from PRSS results in a
value that is uniformly distributed between 0 and 2 inclusive.

A modulus conversion operation can be used to convert that into a sharing in the
prime field.  This requires two multiplications, though some parts of those
multiplications can be avoided; see {{?KIMHC=DOI.10.1007/978-3-319-93638-3_5}}.

Three bits are sampled by each pair of parties.  These are turned into three
shared values, where two of the shared values are filled with zeros. The
exclusive OR of these three values is computed using two multiplications in the
form: `x⊕y = x + y - 2xy`.  This produces a three-way replicated sharing of a
bit in the prime field.

Shares can then be aggregated through simple addition.


### Two Party Protocols

Obtaining multiple random bits in a two party protocol might involve the use of
an oblivious transfer protocol.  Ideally, these are obtained in a large prime
field so that addition is free.

Details of OT protocol TBD.


# Performance Characteristics

A binomial function is relatively inexpensive to compute in MPC.


## Cost Analysis {#cost}

With large epsilon and delta values (that is, low privacy) the use of the
binomial mechanism can be very efficient.  However, smaller values for epsilon
or delta can require significant numbers of Bernoulli trials.

The following table shows some typical values and the resulting number of
trials, along with approximate values for the quantization scaling factor (`s`)
and error.

| epsilon | delta |   N   |   s   | error |
|--------:|------:|------:|------:|------:|
| 3       | 10e-6 | TODO  | TODO  | TODO  |
| 1       | 10e-6 | TODO  | TODO  | TODO  |
| 0.1     | 10e-6 | TODO  | TODO  | TODO  |


## Comparison with Alternative Approaches {#comparison}

Two other approaches that should be compared with are:

* simply having each helper party add noise independently {{?DWORK}}

* amplification by shuffling {{?SHUFLDP=DOI.10.1007/978-3-030-17653-2_13}} where
  local DP is added by clients and used to get a central DP guarantee

A binomial will alway give better privacy/utility trade offs compared to
independent noise.  An MPC system has to ensure that `t` out of `P` parties can
reveal their shares without degrading the privacy of outputs.  Consequently, the
noise that each party adds needs to be proportional to `P/(P-t)` times the
target amount, assuming that noise can be simply added.  For a three party
honest majority system, `P` is 3 and `t` is 1, producing 50% more noise than is
ideal.  For a two party system, the amount of noise needs to be doubled.

Shuffling and any scheme that makes use of noised inputs results in noise that
increases in magnitude as the number of inputs increases, which degrades
utility.  The binomial mechanism does not result in any additional noise.



# Security Considerations

TODO


# IANA Considerations

This document has no IANA considerations.


--- back

# Acknowledgments

TODO
