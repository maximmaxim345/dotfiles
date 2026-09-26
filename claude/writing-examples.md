# Writing examples

Real comments and PR descriptions I wrote, lightly cleaned up. They show my
voice, not templates: match the tone and rhythm, and let the content and
length follow the situation.

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
