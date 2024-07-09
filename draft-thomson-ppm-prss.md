---
title: "High Performance Pseudorandom Secret Sharing (PRSS)"
abbrev: "PRSS"
category: std

docname: draft-thomson-ppm-prss-latest
submissiontype: IETF
consensus: true
v: 3
area: "Security"
workgroup: "Privacy Preserving Measurement"
keyword:
 - prng
 - next generation
 - unicorn
 - sparkling distributed ledger
venue:
  group: "Privacy Preserving Measurement"
  type: "Working Group"
  mail: "ppm@ietf.org"
  arch: "https://mailarchive.ietf.org/arch/browse/ppm/"
  github: "private-attribution/i-d"
  latest: "https://private-attribution.github.io/i-d/draft-thomson-ppm-prss.html"

author:
 -
    name: Martin Thomson
    organization: Mozilla
    email: mt@lowentropy.net
 -
    name: Ben Savage
    organization: Meta
    email: btsavage@meta.com

normative:

informative:


--- abstract

Pseudorandom secret sharing (PRSS) enables the generation of a large number of
shared pseudorandom values from a single shared seed.  This is useful in
contexts where a large amount of shared randomness is needed, such as
multi-party computation (MPC).


--- middle

# Introduction

A number of protocols benefit from having some means by which protocol entities
agree on a random value.  This is particularly useful in multi-party computation
(MPC), such as the three-party, honest majority setting, where many protocols
rely on being able to generate large amounts of shared randomness.

Pseudorandom secret sharing (PRSS) {{?CDI05=DOI.10.1007/978-3-540-30576-7_19}}
is a means of non-interactively establishing multiple shared values from a
single shared secret.  This document describes a concrete PRSS protocol that can
efficiently produce large quantities of shared randomness.

This protocol is parameterized and offers algorithm agility.  This protocol
combines a chosen key encapsulation method (KEM) and key derivation function
(KDF) to generate shared secrets.  These shared secrets form the basis of a
randomness context ({{context}}) in which a chosen lightweight pseudorandom
function (PRF) is used to generate large amounts of shared randomness.  Each
randomness context can either be used as a sequential source of randomness
{{sequential}} or as an indexed source {{indexed}}, depending on need.


## Two-Party Protocol

This document describes a PRSS protocol for two parties.  The set of KEMs
defined only work in a two-party context.  If the goal is to create randomness
that is shared with more than one entity, group key exchange methods, such as
MLS {{?MLS=RFC9420}}, could be adapted as a means of key agreement, retaining
the other elements of this protocol unchanged.


# Conventions and Definitions

{::boilerplate bcp14-tagged}

[participant]: #
[participants]: #participant

This document uses the term "participant" to refer to entities that execute the
protocol.
{: anchor="participant"}

Notation for KEM and KDF functions is taken from {{!HPKE=RFC9180}}.  `e =
I2OSP(n, i)` and `i = OS2IP(e)` functions are taken from {{!RSA=RFC8017}} and
describe encoding and decoding non-negative integers to and from a byte string,
respectively, using network byte order.  `rev()` reverses the order of a
sequence of bytes; `concat()` concatenates multiple sequences of bytes; `xor()`
computes the exclusive or of byte strings or integers of the same type;
`x[a..b]` takes a range of bytes indexed from `a` (inclusive) to `b` (exclusive)
from `x`.


# Overview

A PRSS begins with the establishment of a shared secret.  This protocol uses a
KEM to establish this value.  This is the only communication that occurs between
participants; see {{fig-kex}} and {{kex}}.

~~~ aasvg
   +----------+               +----------+
   |  Sender  |               | Receiver |
   +----+-----+               +----+-----+
        |                          |
        |<---------- pk -----------+
        |                          |
        +---------- enc ---------->|
        |                          |
~~~
{: #fig-kex title="Key Agreement"}

From this shared secret, a KDF is used to generate one or more randomness
contexts; see {{context}}.  Each randomness context can be used independently to
produce many random values through the use of a PRF; see {{fig-context}} and
{{prf}}.

~~~ aasvg
shared secret
      |
      |
      v
   Extract()
      |
      |
      |\
      | `--> Expand(secret, info_0) --> PRF(context_0, 0)
      |                             --> PRF(context_0, 1)
      |                             --> PRF(context_0, 2)
      |                             --> PRF(context_0, 3)
      |                             --> PRF(context_0, 4)
      |                             --> PRF(context_0, 5)
      |                                 ...
      |\
      | `--> Expand(secret, info_1) --> PRF(context_1, 0)
      |\
      | `--> Expand(secret, info_2) --> PRF(context_2, 0)
     ...
~~~
{: #fig-context title="PRSS Key Schedule"}

This document describes both sequential ({{sequential}}) and indexed
({{indexed}}) access to randomness contexts, with different sampling methods
({{sampling}}).


# Key Agreement {#kex}

The first stage of the protocol is key agreement.  In this phase, participants
communicate and establish a shared secret.

Protocol participants are assumed to have a means of authenticating each other.
A confidential communications channel is not necessary, though the use of TLS
{{?TLS=RFC8446}} for authentication purposes will also provide confidentiality
in most cases.

This document uses the system of describing, naming, and identifying KEMs
defined in {{!HPKE=RFC9180}}.  For use in PRSS, a KEM is first chosen for use.
KEM identifiers from {{Section 7.1 of !HPKE}} are used for identification and
can be used in negotiation.

Once a KEM is chosen, one participant is assigned the "sender" role; the other
participant becomes the "receiver".

The receiver commences by generating a KEM key pair as follows:

~~~ pseudocode
def sk, pk_bytes = KeyGen(kem):
    sk, pk = kem.GenerateKeyPair()
    pk_bytes = kem.SerializePublicKey(pk)
~~~

The receiver advertises their public key to the sender by transmitting
`pk_bytes`.  The sender then encapsulates the KEM shared secret as follows:

~~~ pseudocode
def ss, enc = Send(kem, pk_bytes):
    pk = kem.DeserializePublicKey(pk_bytes)
    ss, enc = kem.Encap(pk)
~~~

The sender then sends the encapsulated public key, `enc`, to the receiver.  The
receiver decapsulates this value to obtain the shared secret, `secret`:

~~~ pseudocode
def ss = Receive(kem, sk, enc):
    ss = kem.Decap(enc, sk)
~~~

This produces a value, `ss`, that is `Nsecret` bytes in length.


# Randomness Contexts {#context}

The single shared secret that is produced by a KEM is not suitable for use as a
source of randomness.  A key derivation function (KDF) is used to first extract
randomness from the secret and then to expand it for use in different contexts.

A randomness context is a concept that is defined by protocols that use PRSS.
Each context is identified by a unique string of bytes.  This string is passed
to the KDF to produce a shared value that is unique to that context.

This document uses the system of describing, naming, and identifying KEMs
defined in {{!HPKE=RFC9180}}.  A KDF is first chosen for use.  KDF identifiers
from {{Section 7.2 of !HPKE}} are used for identification and can be used in
negotiation.


## Entropy Extraction {#extract}

A labeled method of entropy extraction is used by this document to ensure that
the randomness provided is bound to both the chosen protocol parameters (KEM,
KDF, and PRF) as well as the values chosen by participants during key agreement.

Each participant constructs a byte sequence by concatenating the following
sequences of bytes:

1. The ASCII encoding {{!ASCII=RFC0020}} of the string "PRSS-00".

2. The identifier for the chosen KEM from {{Section 7.1 of HPKE}}, encoded in
   two bytes in network byte order.

3. The identifier for the chosen KDF from {{Section 7.2 of HPKE}}, encoded in
   two bytes in network byte order.

4. The identifier for the chosen PRF from {{prf}}, encoded in two bytes in
   network byte order.

5. A two byte encoding of the KEM parameter `Npk` in network byte order.

6. The value of `pk_bytes`, the public key from the receiver.

7. A two byte encoding of the KEM parameter `Nenc` in network byte order.

8. The value of `enc`, the key encapsulation from the sender.

Note:

: Draft versions of this protocol will be identified as "PRSS-00".  The suffix
  of this string matches the draft revision in which the scheme last changed.
  The string will not be updated unless the scheme changes in an incompatible
  fashion.  A final version might either omit this suffix or include a different
  string.

This byte sequence is provided as the `ikm` input to the `Extract()` function of
the chosen KDF.  The shared secret, `ss`, is provided as the `salt` input, as
follows:

~~~ pseudocode
def extracted = LabeledExtract(kem, kdf, prf, ss, pk_bytes, enc):
    label = concat(
            ascii("PRSS-00"),
            I2OSP(kem.id, 2),
            I2OSP(kdf.id, 2),
            I2OSP(prf.id, 2),
            I2OSP(kem.Npk, 2),
            pk_bytes,
            I2OSP(kem.Nenc, 2),
            enc,
          )
    extracted = kdf.Extract(salt = ss, ikm = label)
~~~

This process extracts shared entropy that is bound to this protocol and the
context in which it was created.


## Creating Randomness Contexts

A randomness context is identified by a byte sequence.  Applications that use
PRSS need to describe how each randomness context it uses is identified.
Participants with the same shared entropy and the same randomness context
identifier will produce the same randomness.

A randomness context is produced by invoking the `Expand()` function of the
chosen KDF, passing the shared entropy generated in {{extract}} as the `prk`
input, the byte sequence that identifies the context (`ctx\_id`) as the `info`
input, and the PRF parameter `Nk` as the `L` input (see {{prf}}), as follows:

~~~ pseudocode
def context = Context.new(kdf, prf, extracted, ctx\_id):
    context = kdf.Expand(prk = extracted, info = ctx\_id, L = prf.Nk)
~~~

The expanded entropy produced by this process is the only information that is
essential for a randomness context, though a real instantiation might also track
which KEM, KDF, and PRF are used.


# Pseudorandom Function {#prf}

A PRF is instantiated with a secret key, `k`, and provides a single function
`PRF(i)`.

This document adapts the PRF interface to take a non-negative integer as input
and to produce a non-negative integer as output.  New PRF definitions MUST
define three parameters:

* the size of the key (`Nk`),
* the maximum allowed value for the input (`Mi`), and
* the maximum value that can be produced as output (`Mo`).

Importantly, the maximum input value SHOULD reflect a limit that is based on
keeping attacker advantage negligible relative to an ideal PRF.  Any advantage
needs to be bounded when an attacker is able to obtain output values for all
input values between 0 (inclusive) and that maximum (exclusive).  The maximum
input (`Mi`) is therefore likely to be less than the underlying function might
otherwise permit.

This assumes the usage modes from {{modes}}; alternative usage modes that pass
inputs that are randomized or sparse across the entire input space of the
underlying function are possible, but these have not been specified.

Each PRF is identified by a two-byte identifier, allocated using the process in
{{iana}}.


## Cached-Key AES PRF {#aes}

This document defines a PRF based on that described in
{{?GKWY20=DOI.10.1109/SP40000.2020.00016}}.  This provides a PRF that has
circular correlation robustness.

This PRF uses the AES function, either AES-128 or AES-256, as defined in
{{!AES=DOI.10.6028/NIST.FIPS.197}}.  Both of these functions accept a 16 byte
input.  The primary difference in these functions is the size of the key;
AES-128 uses a 16 byte key, whereas AES-256 uses a 32 byte key.  This
information is summarized in {{table-prf}}.

| PRF Name | Identifier | Nk | Mi | Mo |
|:--|--:|--:|--:|--:|--:|
| PRF_AES_128 | 0x0001 | 16 | 2<sup>42</sup> | 2<sup>128</sup> |
| PRF_AES_256 | 0x0002 | 32 | 2<sup>43</sup> | 2<sup>128</sup> |
{: #table-prf title="Pseudorandom Function Summary"}

Both AES PRFs use the same process:

1. The input, `i`, is converted to a 16-byte input using a little-endian
   encoding.

2. These bytes are then input to the AES function to produce a 16 byte output.

3. The AES input and output are XORed produce a 16 byte sequence.

4. The byte sequence is interpreted as an integer using little-endian encoding
   to produce the output randomness.

The process in pseudocode is:

~~~ pseudocode
def randomness = Context.PRF(i):
    input = rev(I2OSP(i, 16))
    output = aes(k, input)
    r_bytes = xor(output, input)
    randomness = OS2IP(rev(r_bytes))
~~~

This step is performance-sensitive, so little endian encoding is chosen to match
the endianness of most hardware that is in use.  This PRF uses a constant key,
which allows implementations to avoid computing the key expansion on each PRF
invocation by caching the expanded values.

Note:

: A similar PRF core is described in {{Section 6.2.2 of
  ?VDAF=I-D.irtf-cfrg-vdaf}}, based on the analysis in
  {{?GKWWY20=DOI.10.1007/978-3-030-56880-1_28}}.  The function described in this
  document operates from a limited input domain that always results in the high
  bits being zero in all cases, making the difference between the two approaches
  negligible; these approaches consequently only differ in the placement of the
  input bits.


# Randomness Usage Modes {#modes}

The same PRF input MUST NOT be used more than once.  Using the same input more
than once will produce identical outputs, which might be exploited by an
attacker.

This section describes two basic access modes for randomness contexts that
provide some safeguards against accidental reuse of inputs:

* A sequential randomness context provides access using a counter; see
  {{sequential}}.

* An indexed randomness context provides concurrent access; see {{indexed}}.

These usages are incompatible; only one mode of access can be used for a given
context.

These usage modes are intended to use a contiguous block of input values,
starting from 0.  The definition of the `Mi` parameter of the PRF function (see
{{aes}}) assumes this usage model.


## Sequential Randomness {#sequential}

In this mode, a counter, starting at zero, is retained with the randomness
context.  Each use of the randomness context first uses that counter as input to
the PRF, then increments it.

~~~ pseudocode
def randomness = Context.next():
    randomness = Context.PRF(this.counter)
    this.counter = this.counter + 1
~~~

This is the simplest access scheme, which is compatible with any sampling
method; see {{sampling}}.


## Indexed Randomness {#indexed}

Indexed randomness ties the use of the randomness context to a sequence of
application records.  The processing of each record is defined to each use `M`
invocations of a certain randomness context.  Therefore, for a given record,
`r`, and usage, `m`, the context is invoked as `context.PRF(r * M + m)`.  The
simplest indexing scheme sets `M` to 1.

Indexed usage is best suited to applications where individual records might be
processed concurrently.  Using indices based on identifiers from an application,
such as record indices, can ensure that the same PRF input is only used once and
frees the randomness context from maintaining its own counter.

Binary sampling ({{binary}}) or oversampling ({{oversampling}}) are best suited
for use with indexed modes.  Rejection sampling ({{rejection}}) is likely to be
unsuitable for an indexed mode because it requires an unpredictable number of
PRF invocations to successfully complete.


# Sampling from the PRF Output {#sampling}

PRSS natively produces a uniformly random value in the range from 0 (inclusive)
to `Mo` (exclusive).

Many applications of PRSS require the selection of a uniform random value from a
fixed range of values.


## Available Randomness

The total randomness available is limited by the entropy from the chosen KEM,
KDF, and PRF.  Each KEM is only able to convey a maximum amount of entropy.
Similarly, each KDF is limited in the amount of entropy it only able to retain.
Finally, each PRF also has limits that might further reduce the maximum entropy
available.

Selecting values from a range that is larger than the available entropy will
affect the uniformity of the output.  In particular, these methods MUST NOT be
used to select from a range that has more values than the `Mo` parameter of the
chosen PRF.

If values larger than `Mo` are needed, the output of multiple PRF invocations
can be combined.  With `k` invocations, the effective value of `Mo` increases to
`Mo`<sup>`k`</sup>.


## Binary Sampling {#binary}

If the range of desired values is a whole power of 2, then simple bit operations
can be used to obtain a value. For a maximum of 2<sup>n</sup> (exclusive),
bitwise operations can produce a value of `randomness & ((1 << n) - 1)`.

Binary sampling produces uniformly random values with the only drawback being
the constraint on its output range.

For small values of `n`, the same PRF invocation could be used to produce
multiple values, depending on the value of `Mo` for the chosen PRF.


## Rejection Sampling {#rejection}

Rejection sampling takes random values until the resulting value is in range.

For values in the range 0 (inclusive) to `m` (exclusive), the value `m` is
rounded up to the next power of 2; that is, an integer `n` is chosen such that
2<sup>n-1</sup> < `m` <= 2<sup>n</sup>.  Then, binary sampling ({{binary}}) is
applied repeatedly for this larger range until the resulting value is less than
`m`.

Rejection sampling provides uniform randomness across the range from 0 to `m`
without bias.  However, rejection sampling can require an indefinite number of
PRF invocations to produce a result.  Rejection is more likely -- and so the
expected number of PRF invocations increases -- when `m` is closer to
2<sup>n-1</sup> than 2<sup>n</sup>.  This can make rejection sampling unsuitable
for use with indexed randomness ({{indexed}}).

Rejection sampling might be used a limited number of times before falling back
to oversampling ({{oversampling}}), which can reduce oversampling bias while
capping the number of PRF invocations.


## Oversampling {#oversampling}

For a target range that is much smaller than the range of values produced by the
PRF, reducing the PRF output modulo the maximum in the range can produce outputs
with negligible bias.

For example, an application goal might seek to produce values in the prime field
`p` = 2<sup>61</sup> - 1.  Using the AES PRF, where `Mo` is 2<sup>128</sup>, and
reducing its output modulo `p` results in a bias that causes the first 64 values
of the field to be chosen with a probability of about 2<sup>-67</sup> more than
other values. This degree of bias might be acceptable in some applications.

To avoid excessive bias, applications SHOULD NOT use oversampling where the
output is less than 2<sup>48</sup> times smaller than `Mo`.  The output of
multiple PRF invocations could be combined to reduce bias.


# Security Considerations

This document describes a small component of a larger system.  A discussion of
considerations necessary to ensure correct application of the included
techniques is provided in relevant sections.  This section concentrates on a
more general analysis of these mechanisms.

## Usage Limit Analysis

The usage limits in {{aes}} ensure that attacker advantage remains small.
Theorem 4 of {{?GKWY20}} models the underlying permutation function as an ideal
PRP and shows that attacker advantage comprises two components:

* a computational limit of `q^2/(2*2^k)` that is based solely on attacker work
  (`q`) and the key size (`k`) of the permutation

* a usage limit of `2pq/2^b` that provides advantage proportional to the number
  of uses of the PRF (`p`), with the entropy of the pseudorandom function (`b`)
  acting to counteract attacker advantage

The number of uses (`p`) are only affected by the second component, as the first
component is unaffected by usage of the permutation.  However, the first
component guides our assumptions about the number of times the attacker might be
willing to invoke the permutation (`q`). The result shows that statistical security is
provided based on the birthday bound. For instance, `q` being 2<sup>64</sup>
results in a disastrous advantage of 0.5 for the AES-128 key size of 128 bits.
This first term therefore places an upper bound on the value that `q` can take
before an attacker can rely solely on this computational limit.

<!--
2^{-a}/2 >= q^2/2^k/2
2^{-a} >= q^2/2^k
2^{k-a} >= q^2
2^{(k-a)/2} >= q

With this value of q, the second component then becomes:

2^{-a}/2 >= 2pq/2^b
    >= 2p.2^{(k-a)/2}/2^b
    >= 2p.2^{-a/2}.2^{k/2-b}
2^{-a/2}/4/2^{k/2-b} >= p
2^{b-k/2-a/2-2} >= p
p <= 2^{b-(k+a)/2-2}
-->

We use this first component to bound the value of `q` for the second component.
If advantage is equally divided between each component we can bound `q` to be at
most `2\^((k-a)/2)`, where `a` is the desired attacker advantage in bits (that
is, advantage is at most 2<sup>-a</sup>).

Using that value for `q` and an advantage of `(2^a)/2` for the second component
leads to a limit for `p` of `2^(b-(k+a)/2-2)`.  For example, to obtain 40 bits
of security, the value of `p` for AES-128 is limited to 2<sup>42</sup>, which
assumes a value of `q` no more than 2<sup>44</sup>.

For AES-256, the larger key size means that the first component is negligible
for any value of `q`, unless `p` and `a` are both very small.  This is due to
AES-256 having the same 128-bit block size as AES-128.  Consequently, increasing
`q` only reduces the value of `p`.

On this basis, the same `q` value can be used for AES-256 as for AES-128. The
usage limit for AES-256 can be doubled to `2\^(b-(k+a)/2-1)` (2<sup>43</sup> for
40 bits of security; the first component is a negligible 2<sup>-169</sup>).

This analysis models AES as an ideal pseudorandom permutation.


## Formal Analysis

TODO


# IANA Considerations {#iana}

This document establishes a new registry for "PRF Functions", under the grouping
"PRSS".  This registry operates on a "Expert Review" for provisional
registrations or the "Specification Required" policy for permanent registrations
{{!RFC8126}}.  Experts for the registry are advised to reject registrations only
when the requests are invalid, abusive, or duplicative of existing entries.

New entries for the "PRF Functions" registry MUST include the following
information:

Name:

: A short mnemonic for the PRF.

Identifier:

: An identifier from the range 0 to 65535 (inclusive).

Nk:

: The number of bytes in the PRF key.

Mi:

: The maximum value of the PRF input.

Mo:

: The maximum value of the PRF output.

Status:

: Either "permanent" or "provisional".

Specification:

: A reference to a specification for the PRF.  Citing a specification is
  optional for provisional registrations.

Last Updated:

: The date of when the registration was last updated.
{: spacing="compact"}

The name and identifier MUST be unique within this registry.

No special allowance is made for private use or experimentation in this
registry.  People conducting experiments are encouraged to provisionally
register a codepoint so that conflicting use of the same identifier can be
avoided.  New PRFs are encouraged to use an identifier that is selected at
random.  IANA are advised not to perform allocation for identifiers, but to use
the identifier that is provided with the registration.

Provisional registrations MAY be removed on request.  Experts can approve
removal after having first attempted to determine that the value is no longer in
use and attempting to contact registrants.  Two months notice MUST be provided
before removing a registration, even when the original registrant requests
removal.  Any entry that are in standards track RFCs or that has been updated in
the past 24 months cannot be removed.

A request to update an entry can be made at any time; any request only refreshes
the "Last Updated" field can be allowed automatically, without consulting the
assigned experts.

Starting values for the registry are shown in {{table-prf}}; these entries are
given a "permanent" status and entries reference {{prf}} of this document.


--- back

# Alternative Designs

Where a small number of shared secrets is desired, communication can be a good
substitute for the methods described in this document.  Depending on the
context, protocol participants can use one of a range of methods to agree on a
random value.  This might involve the use of the KEM and KDF method described in
{{kex}}, a commit-then-reveal protocol, or one of many alternative protocols.

TLS exporters {{Section 7.5 of ?TLS=RFC8446}} are an existing example of
pseudorandom secret sharing.  TLS exporters are suitable for small numbers of
secrets if a TLS connection is available for use, but TLS exporters are an not
efficient means of generating large amounts of randomness.

In some applications, a TLS exporter might be used in place of the KEM to
produce a shared secret; alternatively, the randomness context identifier might
be provided as context to a TLS exporter so that a randomness context might be
produced directly.


# Application to 2-of-3 Replicated Secret Sharing

This section describes how PRSS might be used to produce replicated shares for
use with replicated secret sharing MPC protocols that use additive or XOR secret
sharing.  {{?CDI05}} describes how to use PRSS for protocols that use polynomial
shares.

The simplest replicated secret sharing involves three participants that are
arranged logically in a ring.  Each participant receives two of the three shares
of values.  In this scheme, each participant has one share in common with the
participant to its left and right respectively.

Executing PRSS in this setting requires use of the protocol in a pairwise
fashion; each participant executes the protocol once with the participant to its
left and once with the participant to its right.  As long as participants agree
on parameters - which randomness context is used ({{context}}), which mode is
used ({{modes}}), which index (if using an indexed mode; {{indexed}}), and the
sampling method ({{sampling}}) - this produces replicated shares of a random
value that is not known to any single participant.

{{?CDI05}} also describes how shares of a known, specific value might be
produced using the same scheme, but this is more trivially accomplished in this
setting by setting a pre-arranged share value to the desired value and all
others to zero.


# Acknowledgments
{:numbered="false"}

TODO acknowledge.
