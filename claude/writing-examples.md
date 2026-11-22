# Writing examples

Rules for anything written for other people under my name, then real comments
and PR descriptions I wrote, lightly cleaned up. The examples show my voice,
not templates: match the tone and rhythm, and let the content and length follow
the situation.

## Rules

- No bold.
- No em or en dashes.
- Links go in a list under a short lead-in ("Superseded by:", "Related:"),
  one per line. In replies to a user's issue and in Discord messages, links go
  inline in the sentence instead.
- State opinions in first person with the reason ("I think X, since Y").
- Don't use "genuinely", "notably", "essentially", "additionally", "crucial",
  "delve", "enhance", "pivotal", "showcase", "underscore" or "serves as", and
  no "not just X, but Y".
- Use plain, common words and the host project's vocabulary. If a word needs
  defining, pick another word. Leave out names the reader has never seen, such
  as our test setups ("sync lab") or terms we made up in the session.
- Lead with what the user sees. Give the cause in one clause and leave out
  internals the diff shows.
- Don't @-mention or name anyone besides the person I'm replying to unless I
  ask.
- Take every number and claim from the full source, never a partial read.
- First drafts of comments, replies and messages for other people are one or
  two sentences, and one when replying in an ongoing Discord or issue thread. PR descriptions follow the length rules in
  `~/.claude/pr-guidelines.md`. Show one version.
- Show each draft (title, description, reply, message) as formatted text in
  chat, under a short label and ended by a horizontal rule, so I see it as it
  will render. Use a fenced code block only for Discord messages or when I ask
  for one to copy.
- In review comments, put each sentence on its own line and prefer a question
  to a verdict. For a decision, write "Should we X? If yes ... If no ...".
- Before showing a draft you wrote, tighten it once as its editor: cut filler,
  a sentence that could stand unchanged in another project's docs, a list of
  three that only sounds complete, and a closing "-ing" phrase that adds no
  fact, and keep the voice of the examples below. Then check it against this
  list and the PR rules in `~/.claude/pr-guidelines.md` (length, a title that
  claims no more than the change does), fix what fails, and show only the
  result.
- When I hand you my draft, keep its structure and wording and only fix what's
  wrong.
- Never attribute words or a stance to me or anyone else that they didn't
  write. When someone's exact point matters, quote it.
- Never state a release plan, a date or a commitment I didn't make, and don't
  write as if an unreleased version exists ("when the next beta releases", not
  "on the next beta").
- When the change picks one design over others we discussed, say in a sentence
  or two why each of the others doesn't work.
- Claim exactly what happens and no more, also in a description's body. For a
  breaking change, give the effect in practice first and the technical caveat
  second.
  - Avoid: "a second server can't start Sendspin at all"
  - Prefer: "a second server on the same host starts without Sendspin"
- Give the technical reason that holds in this repo, never a project's stance
  or another project's decision.
  - Avoid: "we don't plan to support PDM/DSD in Sendspin"
  - Prefer: "a Sendspin server has no way to know whether a player's DAC
    accepts DoP"
- On a PR, say what that PR's code does, not what implementations do in
  general.
- Name the client, device or tool a change was tested with. A throwaway script
  is "a Python script", not "a simulated device".
- Name what a user can install or see (the nightly, the next beta, a setting's
  label), never a branch or an internal name.
- Give a spec requirement its exact strength (MUST, SHOULD or common practice),
  and link the spec section inline when it's the reason to decline a request.
- Write a claim about someone else's work that isn't verified as "I think".
- No thanks or praise in a comment that closes or rejects.
- Say what a step, a test or an extra point is for ("Measure five rooms with a
  calibrated mic, to know that the correction makes them sound better"), and
  name a step by what happens in it.
- A reference to a time or a state names its event ("has not connected since
  the server started", not "offline since the start").
- Section labels end with a colon ("Problem:").
- Before drafting a reply to someone's issue or report, tell me in a few lines
  what they asked, whether their own fix or diagnosis is right, which release
  has or will have the fix, and whether the issue can be closed.
- When a text I didn't write is out of date, rewrite it from the current state
  instead of patching it.

## Approving a PR

```
Thanks @user!

Only pushed a small fix on top to handle a format flip-flop edge case.
Nice work!
```

```
LGTM.
Tested with a dropped WebSocket and WebRTC connection.
```

## Closing a superseded PR

```
Closing since this PR got superseded by:
- #86
```

## Closing an out-of-scope issue

```
Closing as out of scope since `sendspin-js` currently only supports client initiated connections.
The whole multi server part of the spec is exclusive to server initiated connections.
```

## Replying to a review on my PR

```
Done, added the `psk_category` field instead in this PR.
```

```
That's for a different PR though since it touches multiple roles, I'll write that once #175 is merged.
```

Accepting a reviewer's suggestion:

```
Good catch! Adjusted it with 889ceab.
```

```
Yes, that's what I meant, your wording is clearer. Applied it, thanks!
```

Conceding a reviewer's point:

```
Hmm, yeah. I was assuming the existing field already covered this, but the spec never said so.
So I went ahead and added it as a requirement. Thanks for catching that!
```

```
Hmm, good point. I'll think about this a bit more and open a separate issue or PR.
```

## Replying to a user's issue

```
Thanks for the report! Unfortunately, I couldn't reproduce this on the latest beta. Could you turn on debug logging for the provider, try to reproduce this again and attach the log?
```

```
Thanks for the report! A fixed id can't come back, since it's now tied to the player's identity. If you keep the settings folder on a persistent volume, the player keeps its identity across restarts. Does that cover your use case?
```

## Discord messages

Show each message in its own fenced code block, ready to copy, with its character count, and keep it under 2000 characters. Write PRs and issues as `[#123](<full URL>)` and leave out headings from the report a message answers.

```
I agree these are implementation work rather than spec gaps. A few notes where it touches the spec:
- With [#123](<https://github.com/owner/repo/pull/123>) a server at capacity can leave the field out. Let me know if that doesn't work for your setup.
```

## Asking a reporter for more info

```
I'm having trouble reproducing this myself, since the nightly plays Opus fine on my ESP32 test device.
Since this is an unsupported install, I'd appreciate it if you could try running the latest nightly through our Docker image to see if the stutter still happens there.
If it does, please share the full server log with the Sendspin provider's log level set to verbose, plus the full ESPHome log from the same playback.
```

## Asking a contributor for something

```
Can you do that please? It's easier to discuss changes to the protocol there, since `aiosendspin` isn't the only Sendspin implementation.
```

## Pushing back

```
I don't think this is a valid argument. You could use this argument for just about everything in this specification.

And, implementations (should) prefer using flac instead of 24-bit PCM.
```

## Explaining a deliberate design choice

```
I deliberately duplicated this section so reading the Markdown file of each role is as self contained as possible.
This way, someone implementing just the visualizer and metadata roles doesn't have to read this section about PCM encoding.
```

## Deferring a merge

```
Before we can merge this, FFmpeg needs to be first bumped to 8.0 or higher. `av` raised the minimum required version.

After merging this PR, the base image also needs to be rebuilt.

Let's defer it until a 2.11 beta to avoid breaking things before the 2.10 stable release.
```

## Reporting a regression

```
This PR broke synchronization.

0ms default doesn't work at least for some browser+OS combinations (Safari+macOS definitely is about 200ms out of sync now).
Tested with `yarn dev-server` and MA frontend with a VPE for reference.

Edit: It was just Safari doing Safari things, underreporting the delay by about 100ms.
```

## Inline review comments

```
Can we call it `SafetyLimiterFilter` instead?
DAWs/VSTs usually have limiters that are way more configurable than just a `ceiling` parameter.

I think calling it like that will also reduce confusion if we add it by default.
```

```
I think there's a deadlock possible here, with `retry_initial_connection=True` and `retry_indefinitely=False` and if it never connects.
```

```
Nit: Spelling out `digit_audio.formats` and `digit_audio.max_bytes` makes it a bit easier to understand.
```

```
Dropping the rotation prose also dropped "MUST NOT rotate it on its own", so nothing now forbids a client rotating this spontaneously. Just double checking, is that intentional to keep it completely up to the manufacturer?
```

```
This only covers rejection at the announce, but a transfer can also start while available and then continue after the client goes `available: false`.
If a client tears the transfer down there, the remaining parts hit the "no transfer in flight" rule and close the connection.
```

```
Idea: Does it make sense to check `data.len()` with what is expected by the `VisualizerDataType`? at least in debug builds?
```

```
This should belong in a PR description and/or issue instead of the spec IMO.
```

## PR descriptions

Title: Use fixed 1.5s scheduling horizon on Cast

```
The precision-based tiers (1.5/1/0.5s) caused unnecessarily short horizons during the start of the playback on Cast devices.

Now scheduling is always fixed to 1.5s to prevent stuttering on some devices while the clock hasn't converged yet (like on my Google Home Mini).
```

Title: Bump `aiosendspin` to 5.2.0 to fix slow desyncing at some player sample rates

```
Fixes a bug where spec-compliant Sendspin player implementations slowly drifted at certain sample rates.

At 44.1 kHz, this specifically caused a drift of 1.6 seconds per hour:
- https://github.com/Sendspin/aiosendspin/pull/236

Also prepares for a future option to connect to Sendspin players without mDNS:
- https://github.com/Sendspin/aiosendspin/pull/233
```

Title: Bump `aiosendspin` to 5.1.1 to fix audio stuttering

```
Bumps `aiosendspin` to 5.1.1.

## Resampling stutter

Fixes audio stuttering on players that require resampling (e.g. 44.1kHz/16-bit clients). The drift detection in the standalone resampler was firing on every call with the soxr resampler, rebuilding the graph every time and dropping a significant portion of audio on any resampling target.

See https://github.com/Sendspin/aiosendspin/pull/219 for details.

## Other changes

- Fix timestamp drift after extended playback (https://github.com/Sendspin/aiosendspin/pull/217)
- Avoid reconnect when mDNS re-advertises same endpoint (https://github.com/Sendspin/aiosendspin/pull/216)
```
