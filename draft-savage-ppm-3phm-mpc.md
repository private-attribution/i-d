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

TODO

--- middle

# Introduction

Multiparty Computation (MPC) can perform generic computations over inputs that
are never revealed to any single entity. MPC executes an agreed function,
revealing only the output of that function.

This makes MPC well-suited to handling data that is sensitive or private. MPC in
a three-party honest majority setting, is broadly recognized as being extremely
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
that a dishonest party can disrupt the protocol


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
modulo 2 ring. This ring is referred to throughput as a binary field as it is
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

Each input value (`x`) is split into three shares (`x<sub>1</sub>`, `x<sub>2</sub>`,
`x<sub>3</sub>`), such that `x = x<sub>1</sub> + x<sub>2</sub> + x<sub>3</sub>`. Any
method can be used, but the following process is typical:

~~~ pseudocode
x_1 = random()
x_2 = random()
x_3 = x - x_1 - x_2
~~~

Then, each party in the MPC receives a different set of two values. This
document adopts the convention that P<sub>1</sub> receives (`x<sub>1</sub>`,
`x<sub>2</sub>`), P<sub>2</sub> receives (`x<sub>2</sub>`, `x<sub>3</sub>`), and
P<sub>3</sub> receives (`x<sub>3</sub>`, `x<sub>1</sub>`). From this sharing, no
single party is able to construct the original value (`x`), but the values from
any two parties include all three shares and can be used to reconstruct the
original value.

Some protocols might require that the parties construct a sharing of a value
which is known to all the parties. In that case, the value of `x<sub>1</sub>` is
set to the known value, with `x<sub>2</sub>` and `x<sub>3</sub>` both set to zero.

## Identifying Shares and Parties

This document identifies shares and parties by number. Three parties are
identified as P<sub>1</sub>, P<sub>2</sub>, and P<sub>3</sub>. The first, or
left share, value held by each party is identified with the same subscript.  The
other share, or right share, held by each is the next highest-numbered share
(with `x<sub>1</sub>` being the next highest after `x<sub>3</sub>`). This is
illustrated in {{fig-shares-parties}}:

~~~ aasvg
        x₂  .----.  x₁
       .---|  P₁  |---.
      /     `----'     \
 x₂  /                  \  x₁
 .----.                .----.
|  P₂  |--------------|  P₃  |
 `----'  x₃        x₃  `----'
~~~
{: #fig-shares-parties title="Parties and Shares"}

Three parties are identified as P<sub>1</sub>, P<sub>2</sub>, and P<sub>3</sub>.

The three parties are logically placed in a ring, with higher numbered parties
to the right of lower-numbered parties. P<sub>3</sub> is placed to the left of
P<sub>1</sub>. This means that if a protocol involves sending a value to the
left, P<sub>1</sub> sends the value to P<sub>3</sub>, P<sub>2</sub> sends to
P<sub>1</sub>, and P<sub>3</sub> sends to P<sub>2</sub>. The sending directions
are illustrated in {{fig-send-direction}}.


~~~ aasvg
send                               send
left:       .----.                 right:      .----.
       .-->|  P₁  |---.                   .---|  P₁  |<--.
      /     `----'     \                 /     `----'     \
     /                  v               v                  \
 .----.                .----.       .----.                .----.
|  P₂  |<-------------|  P₃  |     |  P₂  |------------->|  P₃  |
 `----'                `----'       `----'                `----'
~~~
{: #fig-send-direction title="Parties and Sending Directions"}


Protocols are often described in terms of the actions of a single party. The
party to the left of that party is P<sub>-</sub> and the party to the right is
P<sub>+</sub>. Where necessary, the current party is identified as
P<sub>=</sub>.

The two shares that each party holds are referred to as "left" and "right"
shares. The "left" share is identified with a subscript of "-" (e.g.,
x<sub>-</sub>); the numeric identifier for the left share at each party matches
the identifier for that party, so the left share of x that P<sub>1</sub> holds
is named x<sub>1</sub>. The right share is designated with a subscript of "+"
(e.g., y<sub>+</sub>); the numeric identifier for the right share is one higher
than the identifier for the party, so the right share at P<sub>3</sub> is (also)
x<sub>1</sub>.

## Reveal Protocol {#reveal}

The output of a protocol can be revealed by sending all share values to the
entity that will receive the final result. This entity can validate the
consistency of the values it receives by ensuring that the replicated values it
receives are identical. That is, the value of x<sub>1</sub> received from
P<sub>1</sub> is the same as the value of x<sub>1</sub> it receives from
P<sub>3</sub> and so forth. If the value of shares are inconsistent, the
protocol fails. After discarding these duplicated values, the revealed value is
the sum of the shares that it receives.

A value can be revealed by sending adjacent parties the one share value they do
not have. That is, P<sub>1</sub> sends x<sub>1</sub> to P<sub>2</sub> and
x<sub>2</sub> to P<sub>3</sub>; P<sub>2</sub> sends x<sub>2</sub> to
P<sub>3</sub> and x<sub>3</sub> to P<sub>1;</sub> P<sub>3</sub> sends
x<sub>3</sub> to P<sub>1</sub> and x<sub>1</sub> to P<sub>2</sub>. Each party
verifies that they receive the same value twice, and aborts if they do not.

If the protocol is executed correctly, each party learns the revealed value,
which is the sum of the two shares it holds, plus the share that was received.

This basic reveal protocol requires that each party send and receive two
elements. More efficient protocols are possible, but these are not defined in
this document.

## Addition {#addition}

Addition of two values in this setting is trivial and requires no communication
between parties. To add x to y, each party adds their shares. That is, to
compute z = x + y, each party separately computes the sum of the shares they
hold:

~~~ pseudocode
z<sub>-</sub> = x<sub>-</sub> + y<sub>-</sub>
z<sub>+</sub> = x<sub>+</sub> + y<sub>+</sub>
~~~

This produces shares of the sum without requiring communication.

A similar process can be used for multiplication with a value that is known to
all parties, negation, and subtraction.

{:aside}
> Note: Addition in a binary field is the same as subtraction and both are
> equivalent to the XOR operation.

# Multiplication Protocol {#multiplication}

The product of two shared values, x and y, is computed using the following process.

Since x = x<sub>1</sub> + x<sub>2</sub> + x<sub>3</sub> and y = y<sub>1</sub> +
y<sub>2</sub> + y<sub>3</sub> the product z = x \* y can be expanded as:

~~~ pseudocode
z = (x<sub>1</sub> + x<sub>2</sub> + x<sub>3</sub>) \* (y<sub>1</sub> + y<sub>2</sub> + y<sub>3</sub>)
~~~

This can be illustrated with a 3 by 3 table ({{tab-mul}}):

|  |  y₁ | y₂ | y₃ |
|---|---|---|---|
| x<sub>1</sub> | x<sub>1</sub>\*y<sub>1</sub> | x<sub>1</sub>\*y<sub>2</sub> | x<sub>1</sub>\*y<sub>3</sub> |
| x<sub>2</sub> | x<sub>2</sub>\*y<sub>1</sub> | x<sub>2</sub>\*y<sub>2</sub> | x<sub>2</sub>\*y<sub>3</sub> |
| x<sub>3</sub> | x<sub>3</sub>\*y<sub>1</sub> | x<sub>3</sub>\*y<sub>2</sub> | x<sub>3</sub>\*y<sub>3</sub> |
{: #tab-mul title="Multiplication by Parts"}

To compute the product, each party locally computes the sum of three products as follows:

~~~ pseudocode
z<sub>-</sub> = x<sub>-</sub>·y<sub>-</sub> + x<sub>-</sub>·y<sub>+</sub> + x<sub>+</sub>·y<sub>-</sub>
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

The result is a non-replicated sharing of the result `z = z<sub>1</sub> +
z<sub>2</sub> + z<sub>3</sub>`.

To reach the desired state where parties each have replicated shares of z, each
party needs to send its share, z<sub>-</sub>, to the party to its left.

Unfortunately, each party cannot simply send this value to another party, as this would allow the recipient to reconstruct the full input values, x and y, using z<sub>-</sub>. To prevent this, the value of z<sub>-</sub> is masked with a uniformly distributed random mask that is unknown to party P<sub>-</sub>.

Using a source of shared randomness (such as {{PRSS}}), each pair of helpers generates a uniformly distributed random value known only to the two of them. Let r<sub>-</sub> denote the left value (known to P<sub>-</sub>) and r<sub>+</sub> be the right value (known to P<sub>+</sub>).

Each party uses r<sub>-</sub> and r<sub>+</sub> to create a masked value of z<sub>-</sub> as follows:

~~~ pseudocode
z<sub>-</sub> = x<sub>-</sub>·y<sub>-</sub> + x<sub>-</sub>·y<sub>+</sub> + x<sub>+</sub>·y<sub>-</sub> + r<sub>-</sub> - r<sub>+</sub>
~~~

These three mask values sum to zero, so this masking does not alter the result. Importantly, the value of r<sub>+</sub> is not known to P<sub>-</sub>, which ensures that z<sub>-</sub> cannot be used by P<sub>-</sub> to recover x or y. Thus, z<sub>-</sub> is safe to send to P<sub>-</sub>.

Upon receiving a value from its right — which the recipient names z<sub>+</sub> — each helper is now in possession of two-of-three shares, (z<sub>-</sub>, z<sub>+</sub>), which is a replicated secret sharing of the product of x and y.

# Validation Protocol {#validation}

The basic multiplication protocol in {{multiplication}} only offers "semi-honest security". It is "secure up to an additive attack". Validating multiplications allows any additive attack to be detected, ensuring that a protocol is aborted before any result is produced that might compromise the confidentiality of inputs.

## Additive Attack

By "additive attack", we mean that instead of sending the value z<sub>-</sub>, a corrupted party could instead send z<sub>-</sub> + a. In the context of boolean circuits, the only possible additive attack is to add 1.

The multiplication protocol described does not prevent this. Since the value z<sub>-</sub> is randomly distributed, the party (P<sub>-</sub>) that receives this value cannot tell if an additive attack has been applied.

While an additive attack does not result in information about the inputs being revealed, it corrupts the results. If a protocol depends on revealing certain values, this sort of corruption could be used to reveal information that might not otherwise be revealed.

For example, if the parties were computing a function that erases a value unless it has reached some minimum such as:

~~~ python
if total_count > 1000:
    reveal(total_count)
else:
    reveal(0)
~~~

If a corrupted helper wanted to reveal a total_count that was less than 1000, it could add 1 to the final multiplication used to compute the condition total_count > 1000. The result is that values below the minimum are revealed (and values above the minimum are erased), violating the conditions on the protocol.

## Malicious Security

Before any values are revealed, the parties perform a validation protocol. This protocol confirms that all of the multiplications performed were performed correctly. That is, that no additive attack was applied by any party.

If this validation protocol fails, the parties abort the protocol and no values are revealed. All parties destroy the shares they hold.

## Overview of the validation protocol

Each of the parties, P<sub>=</sub>, produces a "Zero Knowledge Proof" (ZKP) that proves all of the multiplications it performed were done correctly. The other two parties, P<sub>-</sub> and P<sub>+</sub>, act as "verifiers" and validate this zero knowledge proof.

When operating in a boolean field, if P<sub>=</sub> followed the protocol correctly, this is how they would compute z<sub>-</sub>

~~~ pseudocode
z_- = x_-·y_- ⊕ x_-·y_+ ⊕ x_+·y_- ⊕ r_- ⊕ r_+
~~~

So the expression:

~~~ pseudocode
x_-·y_- ⊕ x_-·y_+ ⊕ x_+·y_- ⊕ r_- ⊕ r_+ ⊕ z_- = 0
~~~

will hold true if the protocol was followed correctly, but will equal **_one_** if there was an additive attack.

By computing this quantity in a large prime field (not a boolean field), and then summing across all of the multiplications in a batch, we can compute the total number of times an additive attack was applied. So long as the number of multiplication in a validation batch is smaller than the size of the prime field, this approach will detect any deviation from the protocol.

For this protocol, the parties will use the field of integers mod p, where p is the Mersenne prime 2<sup>61</sup>\-1. Other primes could be used, but this value provides good security margins for a large number of multiplications. It also provides several opportunities for optimization on 64-bit hardware.

## Distributed Zero-Knowledge Proofs

The prover needs to prove that for each multiplication in a batch:

~~~ pseudocode
x_-·y_- ⊕ x_-·y_+ ⊕ x_+·y_- ⊕ r_- ⊕ r_+ ⊕ z_- = 0
~~~

The verifier on the left, P<sub>-</sub>, knows the values of:

- `y<sub>-</sub>`
- x<sub>-</sub>
- r<sub>-</sub>
- z<sub>-</sub>

The verifier on the right, P<sub>+</sub>, knows the values of:

- x<sub>+</sub>
- y<sub>+</sub>
- r<sub>+</sub>

This means that the "prover", P<sub>=</sub>, does not need to send any of these values to the verifiers. Verifiers use information they already have to validate the proof.

Since the two verifiers possess all of this information distributed amongst themselves, this approach is referred to as "Distributed Zero Knowledge Proofs".

## Distributed Zero Knowledge Proofs

{{?FLPCP=DOI.10.1007/978-3-030-26954-8_3}} introduces an elegant tool, which only
requires O(logN) communication, for proving expressions of the form:

~~~ pseudocode
sum(i=0..n, u<sub>i</sub> · v<sub>i</sub>) = t
~~~

In the setting where the Prover (P<sub>=</sub>) and the left verifier
(P<sub>-</sub>) both are in possession of the n-vector `u`, the Prover
(P<sub>=</sub>) and the other verifier (P<sub>+</sub>) are in possession of the
n-vector `v`, and the verifiers P<sub>-</sub> and P<sub>+</sub> hold
t<sub>-</sub> and t<sub>+</sub> respectively and `t<sub>-</sub> +
t<sub>+</sub> = t`.

However, the security of this protocol requires the vector elements `u` and `v`
to be members of a large field. So the first step of the validation protocol is
to take a batch of multiplications, and convert them into a dot product of
vectors with elements in a large field.

## Transforming into a large prime field

{{?BINARY=DOI.10.5555/3620237.3620538}} describes how to apply {{?FLPCP}}
efficiently for binary fields.  When binary values are directly lifted into a
large field, the XOR operation can be computed with the expression:

~~~ pseudocode
f(x, y) = x ⊕ y
        = x + y - 2*x*y
        = x*(1 - 2*y) + y
~~~

Using this relation, the expression that must be proven can be converted into a
dot-product of two vectors, one of which is known to both P<sub>=</sub> and
P<sub>-</sub>, the other being known to both P<sub>=</sub> and P<sub>+</sub>.

Rearranging terms:

~~~ pseudocode
x<sub>-</sub> · y<sub>+</sub> ⊕ (x<sub>-</sub> · y<sub>-</sub> ⊕ z<sub>-</sub> ⊕ r<sub>-</sub> ) ⊕ x<sub>+</sub> · y<sub>-</sub> ⊕ r<sub>+</sub> = 0
~~~

Define:

~~~ pseudocode
e<sub>-</sub> = x<sub>-</sub> · y<sub>-</sub> ⊕ z<sub>-</sub> ⊕ r<sub>-</sub>
~~~

Then:

~~~ pseudocode
(x<sub>-</sub> · y<sub>+</sub> ⊕ e<sub>-</sub> ) ⊕ (x<sub>+</sub> · y<sub>-</sub> ⊕ r<sub>+</sub>) = 0
~~~

Using: `x ⊕ y = x*(1 - 2*y) + y`

~~~ pseudocode
(x<sub>-</sub>·y<sub>+</sub>·(1 - 2e<sub>-</sub>) + e<sub>-</sub>) ⊕ (x<sub>+</sub>·y<sub>-</sub>·(1 - 2r<sub>+</sub>) + r<sub>+</sub>) = 0
~~~

Using: x ⊕ y = x + y - 2*x*y

~~~ pseudocode
(x<sub>-</sub>·y<sub>+</sub>·(1 - 2e<sub>-</sub>) + e<sub>-</sub>)
+ (x<sub>+</sub>·y<sub>-</sub>·(1 - 2r<sub>+</sub>) + r<sub>+</sub>)
- 2(x<sub>-</sub>·y<sub>+</sub>·(1 - 2e<sub>-</sub>) + e<sub>-</sub>)(x<sub>+</sub>·y<sub>-</sub>·(1 - 2r<sub>+</sub>) + r<sub>+</sub>) = 0
~~~

Distributing Terms:

~~~ pseudocode
x<sub>-</sub>·(1 - 2e<sub>-</sub>)·y<sub>+</sub> + e<sub>-</sub>
+ y<sub>-</sub>·x<sub>+</sub>·(1 - 2r<sub>+</sub>) + r<sub>+</sub>
- 2x<sub>-</sub>·y<sub>-</sub>·(1 - 2e<sub>-</sub>)·y<sub>+</sub>·x<sub>+</sub>·(1 - 2r<sub>+</sub>) - 2x<sub>-</sub>·(1 - 2e<sub>-</sub>)·y<sub>+</sub>·r<sub>+</sub> - 2e<sub>-</sub>·y<sub>-</sub>·x<sub>+</sub>·(1 - 2r<sub>+</sub>) - 2e<sub>-</sub>·r<sub>+</sub> = 0
~~~

Rearranging terms, and subtracting 1/2 from both sides:

~~~ pseudocode
- 2x<sub>-</sub>·y<sub>-</sub>·(1 - 2e<sub>-</sub>)·y<sub>+</sub>·x<sub>+</sub>·(1 - 2r<sub>+</sub>)
+ y<sub>-</sub>·x<sub>+</sub>·(1 - 2r<sub>+</sub>) - 2e<sub>-</sub>·y<sub>-</sub>·x<sub>+</sub>·(1 - 2r<sub>+</sub>)
+ x<sub>-</sub>·(1 - 2e<sub>-</sub>)·y<sub>+</sub> - 2x<sub>-</sub>·(1 - 2e<sub>-</sub>)·y<sub>+</sub>·r<sub>+</sub>
+ e<sub>-</sub> - 2e<sub>-</sub>·r<sub>+</sub> + r<sub>+</sub> - ½ = - ½
~~~

Factoring allows this to be written as an expression with four terms, each with a component taken from the left (which we will label g) and a component from the right (which we will label h):

~~~ pseudocode
[-2x<sub>-</sub>·y<sub>-</sub>·(1 - 2e<sub>-</sub>)] · [y<sub>+</sub>·x<sub>+</sub>·(1 - 2r<sub>+</sub>)]
+ [y<sub>-</sub>(1 - 2e<sub>-</sub>)] · [x<sub>+</sub>·(1 - 2r<sub>+</sub>)]
+ [x<sub>-</sub>·(1 - 2e<sub>-</sub>)] · [y<sub>+</sub>(1 - 2r<sub>+</sub>)]
+ [-½(1 - 2e<sub>-</sub>)] · [(1 - 2r<sub>+</sub>)] = -½
~~~

Renaming terms as new variables, the result is the dot product of two four dimensional vectors, g and h:

~~~ pseudocode
g<sub>1</sub>·h<sub>1</sub> + g<sub>2</sub>·h<sub>2</sub> + g<sub>3</sub>·h<sub>3</sub> + g<sub>4</sub>·h<sub>4</sub> = -½
~~~

Or alternatively:

~~~ pseudocode
sum(i=1..4, g<sub>i</sub> · h<sub>i</sub>) = -½
~~~

Where P<sub>=</sub> and P<sub>+</sub> both compute `h<sub>i</sub>` as follows:

~~~ pseudocode
h<sub>1</sub> = y<sub>+</sub>·x<sub>+</sub>·(1 - 2·r<sub>+</sub>)
h<sub>2</sub> = x<sub>+</sub>·(1 - 2·r<sub>+</sub>)
h<sub>3</sub> = y<sub>+</sub>·(1 - 2·r<sub>+</sub>)
h<sub>4</sub> = 1 − 2·r<sub>+</sub>
~~~

And P<sub>=</sub> and P<sub>-</sub> both compute g<sub>i</sub> as follows:

~~~ pseudocode
g<sub>1</sub> = -2·x<sub>-</sub>·y<sub>-</sub>·(1 - 2·e<sub>-</sub> )
g<sub>2</sub> = y<sub>-</sub>·(1 - 2·e<sub>-</sub> )
g<sub>3</sub> = x<sub>-</sub>·(1 - 2·e<sub>-</sub> )
g<sub>4</sub> = -½(1 - 2·e<sub>-</sub>)
~~~

And where:

~~~ pseudocode
e<sub>-</sub> = x<sub>-</sub> · y<sub>-</sub> ⊕ z<sub>-</sub> ⊕ r<sub>-</sub>
~~~

In this field, the negative inverse of two (-½) is 1,152,921,504,606,846,975.

## Validating a batch of multiplications {#initial-uv}

Each multiplication therefore produces two vectors of length 4. To validate a batch of m multiplications, the Prover (P<sub>=</sub>), uses this approach to produce two vectors of length 4m.

The Prover P<sub>=</sub> and verifier P<sub>-</sub> both compute the vector u

~~~ pseudocode
u = (g<sub>1</sub><sup>(1)</sup>, g<sub>2</sub><sup>(1)</sup>, g<sub>3</sub><sup>(1)</sup>, g<sub>4</sub><sup>(1)</sup>, …, g<sub>1</sub><sup>(m)</sup>, g<sub>2</sub><sup>(m)</sup>, g<sub>3</sub><sup>(m)</sup>, g<sub>4</sub><sup>(m)</sup>)
~~~

The Prover P<sub>=</sub> and verifier P<sub>+</sub> both compute the vector v

~~~ pseudocode
v = (h<sub>1</sub><sup>(1)</sup>, h<sub>2</sub><sup>(1)</sup>, h<sub>3</sub><sup>(1)</sup>, h<sub>4</sub><sup>(1)</sup>, …, h<sub>1</sub><sup>(m)</sup>, h<sub>2</sub><sup>(m)</sup>, h<sub>3</sub><sup>(m)</sup>, h<sub>4</sub><sup>(m)</sup>)
~~~

If no additive attacks were applied, the dot product of these two vectors should be:

~~~ pseudocode
u · v = -m/2
~~~

## Overview of Recursive Proof Compression

Now that we have expressed the work of the prover as a simple dot product of two
vectors of large field elements, we can use a recursive approach to prove this
expression with O(logN) communication.

The process is iterative, where at each stage there is a pair of vectors, `u`
and `v`, and a target, `t`, where the goal is to prove that `u · v = t`. The
values of `u` and `v` start as described in {{initial-uv}}; with `t` initially
set to a value of `-m/2`.

At each iteration:

1. Select a compression factor `L`.

2. Chunk the vectors `u` and `v` into `s` segments of length `L`.

    1. Each chunk of `u` uniquely defines a polynomial of degree `L - 1` which
       are named `p<sub>i</sub>(x)`, indexed by `i∊[0..s)`.

    2. Each chunk of `v` uniquely defines a polynomial of degree `L - 1` which
       are named `q<sub>i</sub>(x)`, indexed by `i`.

3. The polynomial `G(x)` is defined as: `sum(i=0..s, p<sub>i</sub>(x) · q<sub>i</sub>(x))`

   This polynomial `G(x)` is equivalent to `u · v` so the goal becomes proving that `sum(i=0..L-1, G(i)) = t`.

   In the first iteration, the target value `t` is known by all parties to be
   `-m/2`. In subsequent iterations the target value will be different.

    1. The prover will compute the value of `2L - 1` points on `G(x)`, the
       minimal number required to uniquely define it.

    2. These `2L - 1` points are split into two additive secret-shares
       `G(x)<sub>-</sub>` and `G(x)<sub>+</sub>` and sent to the verifiers
       P<sub>-</sub> and P<sub>+</sub>, respectively. These shares form the
       distributed zero-knowledge proof.

    3. The verifiers verify the proposition using their shares by computing
       `b<sub>-</sub> = t<sub>-</sub> - sum(i=0..L-1, G(x)<sub>-</sub>)` and
       `b<sub>+</sub> = t<sub>+</sub> - sum(i=0..L-1, G(x)<sub>+</sub>)`. They
       send each other the value they compute and confirm that `b<sub>-</sub> +
       b<sub>+</sub> = 0`. If this test fails, the entire protocol is aborted.

4. At this point, the prover could have produced values for `G(0..L-1)` that
   pass this test even if they had performed an additive attack. The proof needs
   to be validated by confirming that `G(r) = sum(i=0..s, p<sub>i</sub>(r) ·
   q<sub>i</sub>(r))` for a randomly selected challenge point `r`. As long as
   the prover cannot control the choice of `r`, the likelihood that the prover
   is dishonest is inversely proportional to the field size.

    1. If we define two new vectors `u’ = <p<sub>0</sub>(r), …,
       p<sub>s-1</sub>(r)>`, and `v’ = <q<sub>0</sub>(r), …,
       q<sub>s-1</sub>(r)>`, then we can rewrite the statement that needs to be
       proven as: `u’ · v’ = G(r)`. This is of the same form as the original
       statement, but with the new vectors `u’` and `v’` having length `L` times
       shorter than the original vectors.

    2. Each of the verifiers can use the values of G(x) that they have received
       to compute a share of G(r) using Lagrange interpolation. These shares
       become their share of a new value for t.

    3. The Fiat-Shamir heuristic can be used to generate `r` by hashing the
       distributed zero knowledge proof. This transforms this protocol from a
       multi-round interactive protocol into a constant round protocol.

5. The vectors `u` and `v` are replaced by `u’` and `v’`, the value of `t` is
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

The prover (P<sub>=</sub>) and the verifier P<sub>-</sub>, chunk the vector
`u` into `s` chunks of length `L`.

~~~ pseudocode
chunk 0: <u<sub>0</sub>, u<sub>1</sub>, …, u<sub>L-1</sub>>
chunk 1: <u<sub>L</sub>, u<sub>L+1</sub>, …, u<sub>2L-1</sub>>
…
chunk s-1: <u<sub>(s-1)L</sub>, u<sub>(s-1)L+1</sub>, …, u<sub>sL-1</sub>>
~~~

If the length of `u` is not divisible by `L`, then the final chunk will be
padded with zeros.

In the first iteration there will be `s = ceil(4m / L)` chunks, as the original
vectors `u` and `v` have length `4m`. In subsequent iterations there will be
fewer chunks.

They will interpret each chunk (i) as L points lying on a polynomial, p<sub>i</sub>(x) of degree L - 1, corresponding to the x coordinates 0, 1, …, L-1, that is to say they will interpret them as p<sub>i</sub>(0), p<sub>i</sub>(1), …, p<sub>i</sub>(L-1).

The Prover (P<sub>=</sub>) and verifier (P<sub>-</sub>) can find the value of p<sub>i</sub>(x) for any other value of x by using Lagrange interpolation.

The Prover will use Lagrange interpolation to compute the value of p<sub>i</sub>(L), p<sub>i</sub>(L+1), …, p<sub>i</sub>(2L-2).

The same process is applied for the vector v.

The Prover (P<sub>=</sub>) and the verifier P<sub>+</sub>, will chunk the vector v into s chunks of length L.

~~~ pseudocode
chunk 0: <v<sub>0</sub>, v<sub>1</sub>, …, v<sub>L-1</sub>>
chunk 1: <v<sub>L</sub>, v<sub>L+1</sub>, …, v<sub>2L-1</sub>>
…
chunk s-1: <v<sub>(s-1)L</sub>, v<sub>(s-1)L+1</sub>, …, v<sub>sL-1</sub>>
~~~

As before, if the length of v is not a multiple of L, the final chunk will be padded with zeros.

They will interpret each chunk as L points lying on a polynomial, q<sub>i</sub>(x), having degree L - 1. Where the x coordinates are 0, 1, …, L-1, which is to say they will interpret these points as q<sub>i</sub>(0), q<sub>i</sub>(1), …, q<sub>i</sub>(L-1).

The Prover (P<sub>=</sub>) and verifier P<sub>+</sub> can find the value of q<sub>i</sub>(x) for any other value of x by using Lagrange interpolation.

The Prover will use Lagrange interpolation to compute the value of q<sub>i</sub>(L), q<sub>i</sub>(L+1), …, q<sub>i</sub>(2L-2).

## Producing the zero knowledge proof

In order to prove that u · v = t, the prover will compute the value of 2L - 1 points on the polynomial G(x), which is defined as:

G(x) = sum(i=1..s, p<sub>i</sub>(x) · q<sub>i</sub>(x))

The prover computes the values of G(0), G(1), …, G(2L-2) by incrementally aggregating the products of p<sub>i</sub>(0), p<sub>i</sub>(1), …, p<sub>i</sub>(2L-21) and q<sub>i</sub>(L), q<sub>i</sub>(L+1), …, q<sub>i</sub>(2L-2), it computes for each chunk (i).

These 2L - 1 points on the polynomial G(x) constitute the zero-knowledge proof that u · v = t.

An equivalent method of proving u · v = t, is to show that sum(i=0..L-1, G(i)) = t

### Masking the zero-knowledge proof

The Prover (P<sub>=</sub>), cannot simply send this zero-knowledge proof to the verifiers, as doing so would release private information. Instead, the prover can produce a two-part additive secret-sharing of these 2L - 1 points, sending one share to each verifier.

The Prover (P<sub>=</sub>) and the right verifier (P<sub>+</sub>) will generate one share using their shared randomness. We will denote this share G(x)<sub>+</sub>. This requires no communication.

The Prover (P<sub>=</sub>) will compute the other share via subtraction, and will send it to the left verifier (P<sub>-</sub>). Transmitting this share G(x)<sub>-</sub>, will require sending 2L - 1 field values, which will require 8 bytes per field value as we are using Mersenne prime 2<sup>61</sup>-1 for our prime field.

### Checking that the proof says the right thing

To check that:

sum(i=0..L-1, G(i)) = t

The left verifier P<sub>-</sub> will compute:

b<sub>-</sub> = t<sub>-</sub> - sum(i=0..L-1, G(i)<sub>-</sub>)

The right verifier P+ will compute:

b<sub>+</sub> = t<sub>+</sub> - sum(i=0..L-1, G(i)<sub>+</sub>)

The two verifiers will reveal these values b<sub>-</sub> and b<sub>+</sub> to one another, so that each can reconstruct the full sum:

b = b<sub>-</sub> + b<sub>+</sub>

They will confirm that b = 0. If it does not, the parties abort and destroy their shares.

### Generating a random challenge {#challenge}

Now that the verifiers have confirmed that the proof says that there was no
additive attack, they need to validate that this was indeed a legitimate
zero-knowledge proof, and not a bogus one that is disconnected from the actual
work the prover did.

To demonstrate that this zero knowledge proof is sound, it suffices to check
that G(r) is correct, for a random field element r, chosen from the range \[L,
p). In other words, it cannot be in the range \[0, L).

To minimize the rounds of communication, instead of having the verifiers select
this random point, we utilize the Fiat-Shamir transformation to produce a
constant-round proof system.

The Prover (P<sub>=</sub>) will hash the zero-knowledge proof shares it has generated onto a field element as follows:

~~~ pseudocode
commitment = SHA256(
  concat(
    SHA256([G(x)]<sub>-</sub>),
    SHA256([G(x)]<sub>+</sub>)
  )
)
r = (bytes2int(commitment[..16]) % (prime - L)) + L
~~~

This computation does not use the entire output of the hash function, just enough to ensure that the value of r has minimal bias. For SHA-256 and a prime field modulo 2<sup>61</sup>-1, the bias is in the order of 2<sup>-67</sup>, which is negligible.

The verifiers generate the same point r independently. Each verifier only has access to one set of shares from G(x) so they each compute a hash of the shares they have. They then send that hash to each other, after which they can compute the full hash value.

Note that one verifier does not need to receive their shares of G(x) from the prover, so they are able to compute their hash before even starting any computation.

Consequently, though each round depends on communication, the total latency is two rounds. In the first, the prover sends shares of G(x) to the first verifier. Concurrently, the second verifier sends a hash of their shares to the first verifier. In the second round, the first verifier sends a hash of their shares to the second verifier.

<!-- TODO: this Fiat-Shamir seems worse than an explicit challenge… -->

### Recursive Proof

So the prover has to prove that `G(r)` is correct for this random challenge.

Recall the definition of G(x):

~~~ pseudocode
G(x) = sum(i=0..s, p<sub>i</sub>(x) · q<sub>i</sub>(x))
~~~

So this amounts to proving that:

~~~ pseudocode
u’ · v’ = G(r)
~~~

Where:

~~~ pseudocode
u’ = <p<sub>0</sub>(r), p<sub>1</sub>(r), …>
v’ = <q<sub>0</sub>(r), q<sub>1</sub>(r), …>
~~~

Note that this is a problem of exactly the same form as the original problem,
except that the length of u’ and v’ is now a factor of L shorter than the
original length of u and v.

The Prover (P<sub>=</sub>) and verifier P<sub>-</sub> use Lagrange
interpolation to compute the value of p<sub>i</sub>(r) for all (i) in the range
0..s and set this as the new vector u’.

Similarly, the Prover (P<sub>=</sub>) and verifier P<sub>+</sub> use Lagrange
interpolation to compute the value of q<sub>i</sub>(r) for all (i) in the range
0..s and set this as the new vector v’.

### The Final Iteration {#final-iteration}

The proof proceeds recursively until the length of the vectors u and v are
strictly less than the compression factor L.

Next, the Prover (P<sub>=</sub>) and left verifier P<sub>-</sub> will generate
a random field value p<sub>mask</sub> using PRSS. Similarly, the Prover
(P<sub>=</sub>) and right verifier P<sub>+</sub> will generate a random field
value q<sub>mask</sub> using PRSS.

The Prover (P<sub>=</sub>) and left verifier P<sub>-</sub> move u<sub>0</sub>
to index L - 1. No data will be lost as the length of u is strictly less than
L. Then they place the value p<sub>mask</sub> at index 0.

The Prover (P<sub>=</sub>) and right verifier P<sub>+</sub> move v<sub>0</sub>
to index L - 1 and place the value q<sub>mask</sub> at index 0.

The Prover will still generate a zero knowledge proof exactly as before, but the
validation of soundness of this proof will proceed differently.

Firstly, when the verifiers compute their shares of b, they must skip the random
weights.

So in the final iteration the left verifier P<sub>-</sub> computes:

~~~ pseudocode
b<sub>-</sub> = t<sub>-</sub> - sum(i=1..L-1, G(i)<sub>-</sub>)
~~~

And the right verifier P<sub>+</sub> computes:

~~~ pseudocode
b<sub>+</sub> = t<sub>+</sub> - sum(i=1,L-1, G(i)<sub>+</sub>)
~~~

The second difference is the way the verifiers validate the soundness of the
zero knowledge proof. In the final iteration the verifier P<sub>-</sub>
computes p<sub>0</sub>(r) and G(r)<sub>-</sub>, while verifier P<sub>+</sub>
computes q<sub>0</sub>(r) and G(r)<sub>+</sub>. Then the verifiers reveal all of
these values to one another, so that they can both directly check that:

~~~
G(r)<sub>-</sub> + G(r)<sub>+</sub> = p<sub>0</sub>(r) · q<sub>0</sub>(r)
~~~

This is why the random masks were necessary in the final iteration. Those ensure
that none of the values p<sub>0</sub>(r), q<sub>0</sub>(r), G(r)<sub>-</sub>,
or G(r)<sub>+</sub> reveal any private information.

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
2<sup>61</sup>-1 validation.  Any sufficiently large prime can be used; see
TODO/below for an analysis of the batch size requirements and security
properties that can be obtained by using this particular prime.

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
- You can’t just use the multiplication protocol without the validation protocol due to the additive attack (explain why)
- Communication security (authentication)
- Constant time and implications thereof
- Fiat-Shamir vs more rounds

# IANA Considerations

This document has no IANA considerations.


--- back

# Acknowledgments

This work is a direct implementation of the protocols described in {{BINARY}},
which builds on a lot of prior academic work on MPC.
