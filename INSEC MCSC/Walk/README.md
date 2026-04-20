# Walk

**Category:** Misc / Steganography
**Given:** `walk.jpg`

A JPEG with a passphrase-protected payload hidden by **steghide**. The passphrase is a long Spanish ASCII-art message that happens to live in `rockyou.txt`.

## Solving process — rule out, then pounce

Before reaching for password lists, eliminate the easy stego placements:

1. `file walk.jpg` — clean 1920×1080 JPEG, no weird markers.
2. Look for appended data after the `FFD9` end-of-image marker → nothing (rules out "ZIP concatenated to JPEG").
3. Check EXIF metadata and JPEG comments → empty (rules out flag-in-metadata).
4. Try `outguess -r walk.jpg out.txt` → fails with a corrupted-length error (rules out outguess).
5. Sample raw LSBs of R/G/B channels → noise consistent with JPEG quantization, no hidden payload (rules out naïve LSB).

That leaves **steghide** as the overwhelming suspect — it's the default choice for passworded JPEG stego, and a 100-point/19-solve challenge implies the password is in a common wordlist.

## Crack with stegseek

```bash
stegseek walk.jpg /usr/share/wordlists/rockyou.txt
```

Two reasons this finishes in seconds on a 14M-word list:

- **stegseek** exploits a weakness in steghide's RNG — the password is fed into a 32-bit seed, so *testing* a password is ~1000× cheaper than actually extracting. The whole rockyou list burns through in a couple of seconds.
- The passphrase is a literal rockyou entry: a giant "hola como estas... spero q re bn... bueno solo pasaba para saludarte..." ASCII-art block from a mid-2000s MySpace/Hi5 profile. Someone used it as their real password; it ended up in the 2009 rockyou.com breach.

Stegseek writes `walk.jpg.out` — that's `flag.txt` with the flag inside.

## The lesson

Real humans pick terrible passwords, even the long weird-looking ones, and those passwords end up in public breach dumps. The generic workflow for easy/medium misc stego:

```
file check → metadata/EXIF → appended data → LSB analysis → steghide + rockyou (stegseek)
```

Only reach for F5 / JSteg / custom LSB walks if that chain fails.
