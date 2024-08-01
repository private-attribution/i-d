---
title: "Efficient Protocols for Binary Fields in the 3-Party Honest Majority MPC Setting"
abbrev: "3 Party MPC"
category: std

docname: draft-savage-ppm-3phm-mpc-latest
submissiontype: IETF
consensus: true
v: 3
area: "Security"
workgroup: "Privacy Preserving Measurement"
keyword:
 - arithmetic
 - polynomial
 - vector
venue:
  group: "Privacy Preserving Measurement"
  type: "Working Group"
  mail: "ppm@ietf.org"
  arch: "https://mailarchive.ietf.org/arch/browse/ppm/"
  github: "private-attribution/i-d"
  latest: "https://private-attribution.github.io/i-d/draft-savage-ppm-3phm-mpc.html"

author:
 -
    name: Ben Savage
    organization: Meta
    email: btsavage@meta.com
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

informative:


--- abstract

A three party, honest majority system provides the most efficient protocols for
Multiparty Computation (MPC).  This document describes a concrete instantiation
of addition and multiplication protocols that provide strong guarantees of
security.  The multiplication protocol provides low communication and
computation costs, with addition being almost free.  Any single dishonest party
is detected with high probability.

--- middle

# Introduction

Multiparty Computation (MPC) can perform generic computations over inputs that
are never revealed to any single entity. MPC executes an agreed function,
revealing only the output of that function.

This makes MPC well-suited to handling data that is sensitive or private. MPC in
a three-party honest majority setting is broadly recognized as being extremely
efficient:

* Addition and subtraction have zero communication cost and negligible
  computation cost.

* Multiplication is possible with low communication and computation complexity.

* Strong guarantees can be made about correctness and confidentiality, relying
  on only information-theoretic assumptions.

This document describes the basic elements required to compute basic MPC
circuits in this setting. This includes the basic elements of the replicated
secret sharing scheme that is used: generating shares, share addition, and
revealing shared values.

The bulk of the document describes a protocol for multiplication over a binary
field. The basic multiplication protocol scales linearly and involves 1 bit of
communication per party.

This basic multiplication protocol does not prevent an additive attack. To deal
with the additive attack, a batched validation protocol is used, which adds a
sub-linear overhead. This protocol comes with significant memory costs and
slightly increased computational costs, but adds negligible communication
overhead and latency when there are many multiplications to validate.


## MPC Protocols in Binary Fields

This document describes a multiplication protocol that is specialized for use
with binary fields; see {{fields}}.

Composing binary operations into a complete MPC system has proven to be more
efficient than alternatives using prime fields in a number of applications. Some
of the components in this document can be applied to rings or larger prime
fields, but the validation process used here has been specialized for use with
binary values.


# Three-Party Honest Majority MPC

A three-party honest majority MPC system performs computations on secret-shared
values using a replicated scheme where each party receives two out of three
additive shares of input values. Strong guarantees are provided regarding the
confidentiality of inputs provided that no pair of parties reveals their shares
to either of the other parties.

The protocols described in this document depend on having three MPC parties
execute them. The protocols described here are secure with abort, even when one
party is not honest.

Concretely, this means that a single dishonest party cannot cause the value of
inputs to be revealed. Also, a single dishonest party cannot alter the output of
any operation without detection. The protocol is aborted if honest parties
detect an error that might indicate the actions of a dishonest party. This means
that a dishonest party can disrupt the protocol.


## MPC Protocol Prerequisites

MPC parties require channels to each of the other parties that provide
confidentiality, integrity and peer authentication. Mutually-authenticated TLS
{{?RFC8446}} provides the necessary capabilities, however, this document does
not define how to arrange communication between parties; protocols that use
these mechanisms need to define how communication between parties is
established.

The multiplication protocol described depends on shared randomness for
efficiency. The protocol depends on having a way for parties to pairwise agree
on random values. MPC parties can execute a coin toss protocol using the
communication channel, however it is considerably more efficient to use
pseudorandom secret sharing {{PRSS}} when there are a large number of
multiplications.

This section describes basic operations of secret sharing ({{sharing}}), reveal
protocol ({{reveal}}), and addition ({{addition}}). Multiplication is more
involved and is the subject of subsequent sections ({{multiplication}},
{{validation}}).


## Fields and Rings {#fields}

The basic multiplication protocol described in {{multiplication}} operates in
any commutative ring, which will be referred to as simply a "ring". A ring is a
group that defines addition and multiplication operations that are both
associative and commutative. A ring has an additive inverse for every element,
which enables subtraction. A ring contains a "zero" element that is an additive
identity plus a "one" element that is a multiplicative identity.

A simple realization of a ring is formed of integers modulo a chosen integer
that is greater than 1.

The validation protocol described in this document (see {{validation}}) uses a
modulo 2 ring. This ring is referred to throughout as a binary field as it is
also a field and it contains two values: 0 and 1. Addition and multiplication in
a binary field correspond to Boolean operations. Addition in a binary field is
equivalent to the Boolean exclusive OR (XOR) operation. Multiplication in a
binary field is equivalent to the Boolean AND operation.

The security properties of the validation protocol depend on the use of a prime
field of sufficient size. Fields support the same operations as rings, adding
multiplicative inversion of elements, which enables a division operation. A
prime field can be realized from integers modulo any prime. The validation
protocol integrates the projection of values in a binary field to a larger prime
field, rather than requiring a separate conversion step.

## Secret Sharing {#sharing}

Each input value (`x`) is split into three shares (`x<sub>1</sub>`, `x_2`,
`x<sub>3</sub>`), such that `x = x<sub>1</sub> + x_2 + x<sub>3</sub>`. Any
method can be used, but the following process is typical:

~~~ pseudocode
x_1 = random()
x_2 = random()
x_3 = x - x_1 - x_2
~~~

Then, each party in the MPC receives a different set of two values. This
document adopts the convention that `P_1` receives (`x<sub>1</sub>`,
`x_2`), `P_2` receives (`x_2`, `x<sub>3</sub>`), and
`P_3` receives (`x<sub>3</sub>`, `x<sub>1</sub>`). From this sharing, no
single party is able to construct the original value (`x`), but the values from
any two parties include all three shares and can be used to reconstruct the
original value.

Some protocols might require that the parties construct a sharing of a value
which is known to all the parties. In that case, the value of `x<sub>1</sub>` is
set to the known value, with `x_2` and `x<sub>3</sub>` both set to zero.

## Identifying Shares and Parties

This document identifies shares and parties by number. Three parties are
identified as `P_1`, `P_2`, and `P_3`. The first, or
left share, value held by each party is identified with the same subscript.  The
other share, or right share, held by each is the next highest-numbered share
(with `x<sub>1</sub>` being the next highest after `x<sub>3</sub>`). This is
illustrated in {{fig-shares-parties}}:

~~~ aasvg
         x₁ .----. x₂  x₂ .----. x₃  x₃ .----. x₁
       .---+  P₁  +------+  P₂  +------+  P₃  +---.
        \   `----'        `----'        `----'   /
         '--------------------------------------'
~~~
{: #fig-shares-parties title="Parties and Shares"}

Three parties are identified as `P_1`, `P_2`, and `P_3`.

The three parties are logically placed in a ring, with higher numbered parties
to the right of lower-numbered parties. `P_3` is placed to the left of
`P_1`. This means that if a protocol involves sending a value to the
left, `P_1` sends the value to `P_3`, `P_2` sends to
`P_1`, and `P_3` sends to `P_2`. The sending directions
are illustrated in {{fig-send-direction}}.


~~~ aasvg
send
left:      .----.      .----.      .----.
       .--+  P₁  |<---+  P₂  |<---+  P₃  |<--.
        \  `----'      `----'      `----'   /
         '---------------------------------'

send
right:      .----.      .----.      .----.
       .-->|  P₁  +--->+  P₂  +--->|  P₃  +--.
        \   `----'      `----'      `----'  /
         '---------------------------------'
~~~
{: #fig-send-direction title="Parties and Sending Directions"}


Protocols are often described in terms of the actions of a single party. The
party to the left of that party is `P_-` and the party to the right is
`P_+`. Where necessary, the current party is identified as
`P_=`.

The two shares that each party holds are referred to as "left" and "right"
shares. The "left" share is identified with a subscript of "-" (e.g.,
`x_-`); the numeric identifier for the left share at each party matches
the identifier for that party, so the left share of `x` that `P_1` holds
is named `x_1`. The right share is designated with a subscript of "+"
(e.g., `y_+`); the numeric identifier for the right share is one higher
than the identifier for the party, so the right share at `P_3` is (also)
`x_1`.

## Reveal Protocol {#reveal}

The output of a protocol can be revealed by sending all share values to the
entity that will receive the final result. This entity can validate the
consistency of the values it receives by ensuring that the replicated values it
receives are identical. That is, the value of `x_1` received from
`P_1` is the same as the value of `x_1` it receives from
`P_3` and so forth. If the value of shares are inconsistent, the
protocol fails. After discarding these duplicated values, the revealed value is
the sum of the shares that it receives.

A value can be revealed by sending adjacent parties the one share value they do
not have. That is, `P_1` sends `x_1` to `P_2` and `x_2` to `P_3`; `P_2` sends
`x_2` to `P_3` and `x_3` to `P_1`; `P_3` sends `x_3` to `P_1` and `x_1` to
`P_2`. Each party verifies that they receive the same value twice, and aborts if
they do not.

If the protocol is executed correctly, each party learns the revealed value,
which is the sum of the two shares it holds, plus the share that was received.

This basic reveal protocol requires that each party send and receive two
elements. More efficient protocols are possible, but these are not defined in
this document.

## Addition {#addition}

Addition of two values in this setting is trivial and requires no communication
between parties. To add `x` to `y`, each party adds their shares. That is, to
compute `z = x + y`, each party separately computes the sum of the shares they
hold:

~~~ pseudocode
z_- = x_- + y_-
z_+ = x_+ + y_+
~~~

This produces shares of the sum without requiring communication.

A similar process can be used for multiplication with a value that is known to
all parties, negation, and subtraction.

{:aside}
> Note: Addition in a binary field is the same as subtraction and both are
> equivalent to the XOR operation.

# Multiplication Protocol {#multiplication}

The product of two shared values, x and y, is computed using the following process.

Since `x = x_1 + x_2 + x_3` and `y = y_1 +
y_2 + y_3` the product `z = x \* y` can be expanded as:

~~~ pseudocode
z = (x_1 + x_2 + x_3) \* (y_1 + y_2 + y_3)
~~~

This can be illustrated with a 3 by 3 table ({{tab-mul}}):

|  |  y₁ | y₂ | y₃ |
|---|---|---|---|
| `x_1` | `x_1\*y_1` | `x_1\*y_2` | `x_1\*y_3` |
| `x_2` | `x_2\*y_1` | `x_2\*y_2` | `x_2\*y_3` |
| `x_3` | `x_3\*y_1` | `x_3\*y_2` | `x_3\*y_3` |
{: #tab-mul title="Multiplication by Parts"}

To compute the product, each party locally computes the sum of three products as follows:

~~~ pseudocode
z_- = x_-·y_- + x_-·y_+ + x_+·y_-
~~~

To visualize this, {{fig-mul}} shows cells labeled with the party responsible for computing that partial product:

~~~ aasvg
        y₁     y₂     y₃            y₁     y₂     y₃
     +-------------+------+      +--------------------+
  x₁ |  P₁         |      |   x₁ |                    |
     |      +------+      |      |      +-------------+
  x₂ |      |             |   x₂ |      |  P₂         |
     +------+             |      |      |      +------+
  x₃ |                    |   x₃ |      |      |      |
     +--------------------+      +------+------+------+

      y₁     y₂     y₃
     +-------------+------+
  x₁ |             |  P₃  |
     |             +------+
  x₂ |                    |
     +------+      +------+
  x₃ |  P₃  |      |  P₃  |
     +------+------+------+
~~~
{: #fig-mul title="Multiplication by Party"}

The result is a non-replicated sharing of the result `z = z_1 + z_2 + z_3`.

To reach the desired state where parties each have replicated shares of `z`, each
party needs to send its share, `z_-`, to the party to its left.

Unfortunately, each party cannot simply send this value to another party, as
this would allow the recipient to reconstruct the full input values, `x` and
`y`, using `z_-`. To prevent this, the value of `z_-` is masked with a uniformly
distributed random mask that is unknown to party `P_-`.

Using a source of shared randomness (such as {{PRSS}}), each pair of helpers
generates a uniformly distributed random value known only to the two of
them. Let `r_-` denote the left value (known to `P_-`) and `r_+` be the
right value (known to `P_+`).

Each party uses `r_-` and `r_+` to create a masked value of `z_-` as follows:

~~~ pseudocode
z_- = x_-·y_- + x_-·y_+ + x_+·y_- + r_- - r_+
~~~

Each of these three mask values are added once and subtracted once, so this
masking does not alter the result. Importantly, the value of `r_+` is not
known to `P_-`, which ensures that `z_-` cannot be used by `P_-`
to recover `x` or `y`. Thus, `z_-` is safe to send to `P_-`.

Upon receiving a value from its right — which the recipient names `z_+` — each
helper is now in possession of two-of-three shares, (`z_-`, `z_+`), which is a
replicated secret sharing of the product of `x` and `y`.


# Validation Protocol {#validation}

The basic multiplication protocol in {{multiplication}} only offers semi-honest
security. It is secure up to an additive attack; see {{additive-attack}}. Validating multiplications
allows an additive attack to be detected, ensuring that a protocol is aborted
before any result is produced that might compromise the confidentiality of
inputs.

## Additive Attack

By "additive attack", we mean that instead of sending the value `z_-`, a corrupted
party could instead send `z_- + a`. In the context of boolean circuits, the only
possible additive attack is to add 1.

The multiplication protocol described does not prevent this. Since the value
`z_-` is randomly distributed, the party (`P_-`) that receives this
value cannot tell if an additive attack has been applied.

While an additive attack does not result in information about the inputs being
revealed, it corrupts the results. If a protocol depends on revealing certain
values, this sort of corruption could be used to reveal information that might
not otherwise be revealed.

For example, if the parties were computing a function that erases a value unless
it has reached some minimum such as:

~~~ python
if total_count > 1000:
    reveal(total_count)
else:
    reveal(0)
~~~

If a corrupted helper wanted to reveal a total_count that was less than 1000, it
could add 1 to the final multiplication used to compute the condition
`total_count > 1000`. The result is that values below the minimum are revealed
(and values above the minimum are erased), violating the conditions on the
protocol.

## Malicious Security

Before any values are revealed, the parties perform a validation protocol. This
protocol confirms that all of the multiplications performed were performed
correctly. That is, that no additive attack was applied by any party.

If this validation protocol fails, the parties abort the protocol and no values
are revealed. All parties destroy the shares they hold.

## Overview of the Validation Protocol

Each of the parties produces a "Zero Knowledge Proof" (ZKP) that proves to the
two other parties (`P_-` and `P_+`) that all of the
multiplications it performed were done correctly. The two other parties act as
"verifiers" and validate this zero knowledge proof.

The validation protocol is therefore executed three times, with each party
acting as a prover.  Each validation can occur concurrently.

When operating in a boolean field, if `P_=` followed the protocol
correctly, this is how they would compute `z_-`:

~~~ pseudocode
z_- = x_-·y_- ⊕ x_-·y_+ ⊕ x_+·y_- ⊕ r_- ⊕ r_+
~~~

This can be restated as:

~~~ pseudocode
x_-·y_- ⊕ x_-·y_+ ⊕ x_+·y_- ⊕ r_- ⊕ r_+ ⊕ z_- = 0
~~~

The left hand side of this expression will equal zero if the protocol was followed
correctly, but it will equal one if there was an additive attack.

Validation is made more efficient by validating multiple multiplications at the
same time.

The above statement can be transformed to yield the result (either zero or one)
as a value in a large prime field {{prime_field_transformation}}. These values
can be summed across all the multiplications in a large batch. The total sum will
be the count of additive attacks applied, which will be zero if the prover correctly
followed the protocol. There will not be any wrapping around so long as the number
of multiplications in the batch is smaller than the prime used to define the field.

For this protocol, the parties will use the field of integers mod `p`, where `p` is a large prime.

## Distributed Zero-Knowledge Proofs

The prover (`P_=`) needs to prove that for each multiplication in a batch:

~~~ pseudocode
x_-·y_- ⊕ x_-·y_+ ⊕ x_+·y_- ⊕ r_- ⊕ r_+ ⊕ z_- = 0
~~~

The left verifier (`P_-`) knows the values of `y_-`, `x_-`,
`r_-`, and `z_-`.

The right verifier (`P_+`) knows the values of `x_+`, `y_+`,
`r_+`.

This means that the prover (`P_=`) does not need to send any of these
values to the verifiers. Verifiers use information they already have to validate
the proof.

Since the two verifiers possess all of this information distributed amongst
themselves, this approach is referred to as "Distributed Zero Knowledge Proofs".

## Distributed Zero Knowledge Proofs

{{?FLPCP=DOI.10.1007/978-3-030-26954-8_3}} describes a system of zero-knowledge
proofs that rely on linear operations. This is expanded in
{{?BOYLE=DOI.10.1007/978-3-030-64840-4_9}} to apply to three-party
honest-majority MPC, requiring only O(logN) communication in total.  These
proofs are able to validate the computation of an inner product, or expressions
of the form:

~~~ pseudocode
sum(i=0..n, u<sub>i</sub> · v<sub>i</sub>) = t
~~~

This depends on the prover (`P_=`) and left verifier (`P_-`)
both possessing the n-vector `u`, the prover (`P_=`) and the right
verifier (`P_+`) possessing the n-vector `v`, and the verifiers
`P_-` and `P_+` jointly holding shares of the target value, `t`
(that is, `P_-` holds `t_-` and `P_-` holds `t_+` such that `t_-
+ t_+ = t`).

However, the security of this protocol requires the vector elements `u` and `v`
to be members of a large field. So the first step of the validation protocol is
to take a batch of multiplications, and convert them into a dot product of
vectors with elements in a large field.

## Transforming into a Large Prime Field {#prime_field_transformation}

{{?BINARY=DOI.10.5555/3620237.3620538}} describes how to apply {{?FLPCP}}
efficiently for binary fields.  When binary values are directly lifted into a
large field, the XOR operation can be computed with the expression:

~~~ pseudocode
f(x, y) = x ⊕ y
        = x + y - 2·x·y
        = x·(1 - 2·y) + y
~~~

Using this relation, the expression that must be proven can be converted into a
dot-product of two vectors, one of which is known to both `P_=` and
`P_-`, the other being known to both `P_=` and `P_+`.

Rearranging terms:

~~~ pseudocode
x_-·y_+ ⊕ (x_-·y_- ⊕ z_- ⊕ r_-) ⊕ x_+·y_- ⊕ r_+ = 0
~~~

Define:

~~~ pseudocode
e_- = x_-·y_- ⊕ z_- ⊕ r_-
~~~

Then:

~~~ pseudocode
(x_-·y_+ ⊕ e_-) ⊕ (x_+·y_- ⊕ r_+) = 0
~~~

Using: `x ⊕ y = x·(1 - 2·y) + y`

~~~ pseudocode
(x_-·y_+·(1 - 2e_-) + e_-) ⊕ (x_+·y_-·(1 - 2r_+) + r_+) = 0
~~~

Using: `x ⊕ y = x + y - 2·x·y`

~~~ pseudocode
(x_-·y_+·(1 - 2e_-) + e_-)
+ (x_+·y_-·(1 - 2r_+) + r_+)
- 2(x_-·y_+·(1 - 2e_-) + e_-)(x_+·y_-·(1 - 2r_+) + r_+) = 0
~~~

Distributing and rearranging terms, plus subtracting 1/2 from both sides,
produces:

~~~ pseudocode
- 2x_-·y_-·(1 - 2e_-)·y_+·x_+·(1 - 2r_+)
+ y_-·x_+·(1 - 2r_+) - 2e_-·y_-·x_+·(1 - 2r_+)
+ x_-·(1 - 2e_-)·y_+ - 2x_-·(1 - 2e_-)·y_+·r_+
+ e_- - 2e_-·r_+ + r_+ - ½ = - ½
~~~

Factoring allows this to be written as an expression with four terms, each with
a component taken from the left and a component from
the right.

~~~ pseudocode
[-2x_-·y_-·(1 - 2e_-)] · [y_+·x_+·(1 - 2r_+)]
+ [y_-(1 - 2e_-)] · [x_+·(1 - 2r_+)]
+ [x_-·(1 - 2e_-)] · [y_+(1 - 2r_+)]
+ [-½(1 - 2e_-)] · [(1 - 2r_+)] = -½
~~~

Components on the left form a vector that can be named `g`, and components on
the right form a vector, `h`. The result is the dot product of two four
dimensional vectors:

~~~ pseudocode
g_1·h_1 + g_2·h_2 + g_3·h_3 + g_4·h_4 = -½
~~~

Alternatively:

~~~ pseudocode
sum(i=1..4, g_i·h_i) = -½
~~~

From this point, each party can compute the vectors that they are able to.

`P_=` and `P_-` both compute `g_i` as follows:

~~~ pseudocode
g_1 = -2·x_-·y_-·(1 - 2·e_-)
g_2 = y_-·(1 - 2·e_-)
g_3 = x_-·(1 - 2·e_-)
g_4 = -½(1 - 2·e_-)
~~~

And where:

~~~ pseudocode
e_- = x_-·y_- ⊕ z_- ⊕ r_-
~~~

`P_=` and `P_+` both compute `h_i` as follows:

~~~ pseudocode
h_1 = y_+·x_+·(1 - 2·r_+)
h_2 = x_+·(1 - 2·r_+)
h_3 = y_+·(1 - 2·r_+)
h_4 = 1 − 2·r_+
~~~

These vectors form the basis of later stages of the proof.

{:aside}
> In the prime field modulo 2<sup>61</sup>-1, the negative inverse of two
> (-2<sup>-1</sup> or -½) is 1,152,921,504,606,846,975.

## Validating a batch of multiplications {#initial-uv}

Each multiplication therefore produces two vectors, with each vector being
length 4. To validate a batch of `m` multiplications, the prover
(`P_=`), forms two vectors of length `4m`.

The prover (`P_=`), and left verifier (`P_-`) both produce the
vector `u` by concatenating the vectors from all multiplications:

~~~ pseudocode
u = (g_1<sup>(1)</sup>, g_2<sup>(1)</sup>, g_3<sup>(1)</sup>, g_4<sup>(1)</sup>,
     g_1<sup>(2)</sup>, g_2<sup>(2)</sup>, g_3<sup>(2)</sup>, g_4<sup>(2)</sup>,
     …
     g_1<sup>(m)</sup>, g_2<sup>(m)</sup>, g_3<sup>(m)</sup>, g_4<sup>(m)</sup>)
~~~

The prover (`P_=`) and right verifier (`P_+`) both compute the vector `v` in the same way:

~~~ pseudocode
v = (h_1<sup>(1)</sup>, h_2<sup>(1)</sup>, h_3<sup>(1)</sup>, h_4<sup>(1)</sup>,
     h_1<sup>(2)</sup>, h_2<sup>(2)</sup>, h_3<sup>(2)</sup>, h_4<sup>(2)</sup>,
     … ,
     h_1<sup>(m)</sup>, h_2<sup>(m)</sup>, h_3<sup>(m)</sup>, h_4<sup>(m)</sup>)
~~~

If no additive attacks were applied by the prover, the dot product of these two vectors should be:

~~~ pseudocode
u\*v = -m/2
~~~

## Overview of Recursive Proof Compression

Now that we have expressed the work of the prover as a simple dot product of two
vectors of large field elements, we can use a recursive approach to prove this
expression with O(logN) communication.

The process is iterative, where at each stage there is a pair of vectors, `u`
and `v`, and a target, `t`, where the goal is to prove that `u·v = t`. The
values of `u` and `v` start as described in {{initial-uv}}; with `t` initially
set to a value of `-m/2`.

At each iteration:

1. Select a compression factor `L`.

2. Chunk the vectors `u` and `v` into `s` segments of length `L`.

    1. Each chunk of `u` uniquely defines a polynomial of degree `L-1` which
       are named `p<sub>i</sub>(x)`, indexed by `i ∊ [0..s)`.

    2. Each chunk of `v` uniquely defines a polynomial of degree `L-1` which
       are named `q<sub>i</sub>(x)`, indexed by `i ∊ [0..s)`.

3. The polynomial `G(x)` is defined as: `sum(i=0..s, p<sub>i</sub>(x) · q<sub>i</sub>(x))`

   For `x ∊ [0..L-1)`, this polynomial `G(x)` computes the inner product of a
   portion of `u` and `v`. So the goal becomes proving that `sum(i=0..L-1, G(i)) = t`.

   In the first iteration, the target value `t` is known by all parties to be
   `-m/2`, so left verifier (`P_-`) sets their share `t_-` to `-m/2` and the right
   verifier `P_+` sets their share `t_+` to zero. In subsequent iterations the
   target value will not be known to both verifiers.

    1. The prover will compute the value of `G(0)`, `G(1)`, ... , `G(2L-2)`,
       the minimal number of points required to uniquely define it.

    2. These `2L-1` points are split into two additive secret-shares
       `G_-(x)` and `G_+(x)` and sent to the verifiers
       `P_-` and `P_+`, respectively. These shares form the
       distributed zero-knowledge proof.

    3. The verifiers each sum together the first `L-1` points they were given:
       `P_-` computes `sum_- = sum(i=0..L-1, G_-(i))`.
       `P_+` computes `sum_+ = sum(i=0..L-1, G_+(i))`.
       As a result, `sum_- + sum_+ = sum(0..L-1, G(i))`.

    4. Now the verifiers verify the proposition `sum(i=0..L-1, G(i)) = t` by having
       `P_-` compute `b_- = t_- - sum_-` and
       `P_+` compute `b_+ = t_+ - sum_+`.
       They send each other these values and confirm that
       `b_- + b_+ = 0`. If this test fails, the entire protocol is aborted.

4. At this point, the prover could have produced values for `G(0..L-1)` that
   pass this test even if they had performed an additive attack. The proof needs
   to be validated by confirming that `G(r) = sum(i=0..s, p<sub>i</sub>(r) ·
   q<sub>i</sub>(r))` for a randomly selected challenge point `r`. As long as
   the prover cannot control the choice of `r`, the likelihood that a dishonest
   prover can cheat without detection is inversely proportional to the field size.

    1. If we define two new vectors `u′ = { p<sub>0</sub>(r), …,
       p<sub>s-1</sub>(r) }`, and `v′ = { q<sub>0</sub>(r), …,
       q<sub>s-1</sub>(r) }`, then we can rewrite the statement that needs to be
       proven as: `u′ · v′ = G(r)`. This is of the same form as the original
       statement, but with the new vectors `u′` and `v′` having length `L` times
       shorter than the original vectors.

    2. `u′` and `v′` need not be communicated, since the prover and left verifier (`P_-`)
       can both compute each value `p<sub>i</sub>(r)` using Lagrange interpolation,
       just as the prover and right verifier (`P_+`) can compute each value `q<sub>i</sub>(r)`.

    3. Each of the verifiers can use the `2L-1` points they received (their share
       of `G(x)`) to compute a share of `G(r)` using Lagrange interpolation. These
       shares become their share of a new value for `t`.

    4. The Fiat-Shamir heuristic can be used to generate `r` by hashing the
       distributed zero knowledge proof. This transforms this protocol from a
       multi-round interactive protocol into a constant round protocol.

5. The vectors `u` and `v` are replaced by `u′` and `v′`, the value of `t` is
   set to `G(r)`, and the next iteration is started.

The recursion ends when the vectors `u` and `v` have length less than `L`.  The
verifiers validate the soundness of the final iteration of the proof in a
simpler, more direct way; see {{final-iteration}}.

## Detailed Validation Algorithm

### Selecting the Compression Factor

For the first iteration, the parties will use a compression factor (`L`) of 32. In
all subsequent rounds they will use a compression factor of 8.

Note: A larger value for `L` increases the compression factor, which reduces the
overall communication cost. However, because the computation of the proof
requires Lagrange interpolation (which is O(L<sup>2</sup>) computation), a
larger compression factor quickly becomes expensive. A slightly larger
compression factor on the first round is possible because there are only a small
number of possible input values, so the work can be reduced with the use of
lookup tables if necessary.

### Producing Polynomials `p(x)` and `q(x)`

The prover (`P_=`) and the left verifier (`P_-`), chunk the vector
`u` into `s` chunks of length `L`.

* chunk 0: <u<sub>0</sub>, u<sub>1</sub>, …, u<sub>L-1</sub>>
* chunk 1: <u<sub>L</sub>, u<sub>L+1</sub>, …, u<sub>2L-1</sub>>
* …
* chunk s-1: <u<sub>(s-1)L</sub>, u<sub>(s-1)L+1</sub>, …, u<sub>sL-1</sub>>

If the length of `u` is not divisible by `L`, then the final chunk will be
padded with zeros.

In the first iteration there will be `s = ceil(4m / L)` chunks, as the original
vectors `u` and `v` have length `4m`. In subsequent iterations there will be
fewer chunks.

They will interpret each chunk as `L` points lying on a polynomial,
`p<sub>i</sub>(x)` of degree `L-1`, corresponding to the `x` coordinates `{ 0,
1, …, L-1 }`, that is to say they will interpret them as `{ p<sub>i</sub>(0),
p<sub>i</sub>(1), …, p<sub>i</sub>(L-1) }`.

The prover (`P_=`) and left verifier (`P_-`) can find the value of
`p<sub>i</sub>(x)` for any other value of `x` using Lagrange interpolation.

The prover (`P_=`) uses Lagrange interpolation to compute the values `{
p<sub>i</sub>(L), p<sub>i</sub>(L+1), …, p<sub>i</sub>(2L-2) }`.

The same process is applied for the vector `v` with the right verifier, (`P_+`).

The prover (`P_=`) and the right verifier (`P_+`), chunk the vector `v`
into `s` chunks of length `L`.

* chunk 0: <v<sub>0</sub>, v<sub>1</sub>, …, v<sub>L-1</sub>>
* chunk 1: <v<sub>L</sub>, v<sub>L+1</sub>, …, v<sub>2L-1</sub>>
* …
* chunk s-1: <v<sub>(s-1)L</sub>, v<sub>(s-1)L+1</sub>, …, v<sub>sL-1</sub>>

As before, if the length of `v` is not a multiple of `L`, the final chunk will
be padded with zeros.

Each chunk is interpreted as `L` points on a polynomial. From this the values `{
q<sub>i</sub>(L), q<sub>i</sub>(L+1), …, q<sub>i</sub>(2L-2) }` are found using
using Lagrange interpolation.

## Producing the Zero Knowledge Proof

In order to prove that `u\*v = t`, the prover will compute the value of `2L-1`
points on the polynomial `G(x)`, which is defined as:

~~~ pseudocode
G(x) = sum(i=1..s, p_i(x) · q_i(x))
~~~

The prover computes the values of `{ G(0), G(1), …, G(2L-2) }` by incrementally
aggregating the products of `{ p<sub>i</sub>(0), p<sub>i</sub>(1), …,
p<sub>i</sub>(2L-21) }` and `{ q<sub>i</sub>(L), q<sub>i</sub>(L+1), …,
q<sub>i</sub>(2L-2) }`, for each chunk.

These `2L-1` points on the polynomial `G(x)` constitute the zero-knowledge proof
that `u·v = t`.

An equivalent method of proving `u·v = t`, is to show that `sum(i=0..L-1, G(i))
= t`.

### Masking the Zero-Knowledge Proof

The prover (`P_=`), cannot simply send this zero-knowledge proof to the
verifiers, as doing so would release private information. Instead, the prover
produces a two-part additive secret-sharing of these `2L-1` points, sending one
share to each verifier.

The prover (`P_=`) and the right verifier (`P_+`) generate one
share using their shared randomness, which means that no communication is
needed.  This share is denoted `G_+(x)`.

The prover (`P_=`) computes the other share via subtraction.  That is,
`G_-(x) = G(x) - G_+(x)`.  This value is sent to the left verifier
(`P_-`). Transmitting this share `G_-(x)` involves sending `2L-1` field
values.

### Validating the Proof Increment

To check that `sum(i=0..L-1, G(i)) = t`, the left verifier (`P_-`)
computes:

~~~ pseudocode
b_- = t_- - sum(i=0..L-1, G_-(i))
~~~

Similarly, the right verifier (`P_+`) computes:

~~~ pseudocode
b_+ = t_+ - sum(i=0..L-1, G_+(i))
~~~

The two verifiers will reveal these values `b_-` and `b_+` to one another, so
that each can reconstruct the full sum, `b = b_- + b_+`.

Each confirms that `b` is zero. If it is not, the parties abort and destroy
their shares.

### Random Challenge {#challenge}

Now that the verifiers have confirmed that the proof says that there was no
additive attack, they need to validate that this was indeed a legitimate
zero-knowledge proof.  The prover knows the value of `t`, even if each verifier
only has shares of `t` after the first round.  Therefore, it is trivial for a
prover to falsify `G(x)`.

To demonstrate that the prover has provided a valid `G(x)`, a random field
element, `r`, is chosen from the range `[L, p)` (that is, a value that is not
part of the proof).  The prover then has to show that the value of `G(r)`
matches what the verifiers hold.  The verifiers could jointly compute this value
using the values of `p_i(x)` and `q_i(x)`.

The key requirement in choosing `r` is that the prover cannot influence the
choice.

### Fiat-Shamir Challenge Selection

To minimize the rounds of communication, instead of having the verifiers select
this random point, we utilize the Fiat-Shamir transform to produce a
constant-round proof system.

The prover (`P_=`) hashes the zero-knowledge proof shares it has
generated onto a field element as follows:

~~~ pseudocode
commitment = SHA256(
  concat(
    SHA256([G(x)]_-),
    SHA256([G(x)]_+)
  )
)
r = (bytes2int(commitment[..16]) % (prime - L)) + L
~~~

This computation does not use the entire output of the hash function, just
enough to ensure that the value of r has minimal bias. For SHA-256 and a prime
field modulo 2<sup>61</sup>-1, the bias is in the order of 2<sup>-67</sup>,
which is negligible.

The verifiers generate the same point `r` independently. Each verifier only has
access to one set of shares from `G(x)` so they each compute a hash of the shares
they have. They then send that hash to each other, after which they can concatenate
the two hash values and compute the challenge point.

Note that one verifier does not need to receive their shares of `G(x)` from the
prover, so they are able to compute their hash before even starting any
computation.

Consequently, though each round depends on communication, the total latency is two rounds. In the first, the prover sends shares of G(x) to the left verifier. Concurrently, the right verifier sends a hash of their shares to the left verifier. In the second round, the left verifier sends a hash of their shares to the right verifier.

<!-- TODO: this Fiat-Shamir seems worse than an explicit challenge… -->

### Recursive Proof

At the end of each round, the prover is left with the task of proving that
`G(r)` is correct based on the random challenge. `r`.

Recall the definition of `G(x)`:

~~~ pseudocode
G(x) = sum(i=0..s, p<sub>i</sub>(x)·q<sub>i</sub>(x))
~~~

This is equivalent to providing that `u′ · v′ = G(r)`, where:

~~~ pseudocode
u′ = <p<sub>0</sub>(r), p_1(r), …>
v′ = <q<sub>0</sub>(r), q_1(r), …>
~~~

This is a problem of exactly the same form as the original problem, except that
the length of `u′` and `v′` is now a factor of `L` shorter than the original
length of `u` and `v`.

The prover (`P_=`) and left verifier (`P_-`) use Lagrange interpolation
to compute the value of `p<sub>i</sub>(r)` for all chunks in the range `0..s`
and set this as the new vector `u`.

Similarly, the prover (`P_=`) and right verifier (`P_+`) use Lagrange
interpolation to compute the value of `q<sub>i</sub>(r)` and set this as the new
vector `v`.

The target value `t` is set to `G(r)`.  The two verifiers do not learn `G(r)`.
Instead, each uses Lagrange interpolation to compute a share of `G(r)`.  That
is:

~~~ pseudocode
t_- = lagrange\_interpolate(r, [G_-(0), G_-(1), ..., G_-(2L-2)])
t_+ = lagrange\_interpolate(r, [G_+(0), G_+(1), ..., G_+(2L-2)])
~~~


### The Final Iteration {#final-iteration}

The proof proceeds recursively until the length of the vectors `u` and `v` are
strictly less than the compression factor `L`.

Next, the prover (`P_=`) and left verifier (`P_-`) jointly
generate a random field value `p_m` using shared secrets. Similarly, the prover
(`P_=`) and right verifier (`P_+`) generate a random field value
`q_m` using shared secrets.

The prover (`P_=`) and left verifier (`P_-`) move `u_0` to index
`L-1`. No data will be lost as this replaces a zero value; the length of `u` is
strictly less than `L`.  The value at index 0 is replaced with `p_m`.

The prover (`P_=`) and right verifier (`P_+`) move `v_0`
to index `L-1` and place the value `q_m` at index 0.

The prover generates a zero knowledge proof from these polynomials exactly as
before, sending each verifier `2L-1` shares of `G(x)`.  The process of
validation then proceeds differently.

Firstly, when the verifiers compute their shares of `b`, they ignore the random
value at index 0 of `G(x)`.  That is:

~~~ pseudocode
b_- = t_- - sum(i=1..L-1, G_-(i))
b_+ = t_+ - sum(i=1..L-1, G_+(i))
~~~

Verifiers confirm that `b_- + b_+` is zero by exchanging their shares of `b`.

Finally, the left verifier (`P_-`)
computes both `p_0(r)` and `G_-(r)`, right verifier (`P_+`)
computes `q_0(r)` and `G_+(r)`, and then the verifiers reveal all of
these values to each other.  They then both verify that:

~~~ pseudocode
G_-(r) + G_+(r) = p_0(r) · q_0(r)
~~~

The addition of random masks (`p_m` and `q_m`) ensure that revealing `G(r)` in
this way does not reveal anything about the value of the polynomials held by the
other party.  Revealing `q_0(r)`, which was computed from the random values,
only confirms that the prover did not cheat.


# Conditions of Usage

This protocol requires integration into a larger protocol, which will need to:

* set or negotiate parameters,
* provide communication channels,
* agree on shared secrets, and
* arrange the multiplications that are to be validated into batches.

## Recommended Parameters

This document recommends several parameters, which are used in the security
analysis.  Alternative parameters can be used, provided that they meet the
stated requirements.

For shared secrets, pseudorandom secret sharing {{PRSS}} is used.  For PRSS
parameters, HPKE {{?RFC9180}} with DHKEM(X25519, HKDF-SHA256), HKDF-SHA256, and
AES-128-GCM is RECOMMENDED, with the same KDF being used for PRSS and AES-128 as
the PRP.

For validation, the prime field used is modulo the Mersenne prime
2<sup>61</sup>-1.  Any sufficiently large prime can be used, but this
value provides both good performance on 64-bit hardware and useful security
margins for typical batch sizes; see TODO/below for an analysis of the batch
size requirements and security properties that can be obtained by using this
particular prime.

The Fiat-Shamir transform {{challenge}} used in the validation proofs can use
SHA-256.  However, any preimage and collision-resistant hash function can be
used provided that it has a enough output entropy to avoid bias in the selected
field value.


# Performance Characteristics

TODO

- Communication - number of bits sent/received
- Computation - how many times you invoke PRSS
- Vectorization - why it is useful and good
- How to multiply in parallel - sending and receiving, stalling, etc…
- Memory requirements
  - Compression factor and choice
  - Trade-offs - time/memory (factor of 64 during generation of r, for Fiat-Shamir version)
- Multiple rounds or Fiat-Shamir

# Security Considerations

TODO

- Parameter choice and security margins
  - Talk about trade-off between attack success probability and prime size.
  - Show equation for how many bits of security you get when validating N multiplications
- You can't just use the multiplication protocol without the validation protocol due to the additive attack (explain why)
- Communication security (authentication)
- Constant time and implications thereof
- Fiat-Shamir vs more rounds

# IANA Considerations

This document has no IANA considerations.


--- back

# Acknowledgments

This work is a direct implementation of the protocols described in {{BINARY}},
which builds on a lot of prior academic work on MPC.
