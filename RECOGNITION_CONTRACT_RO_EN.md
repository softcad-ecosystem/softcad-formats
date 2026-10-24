# SoftCAD File Family Recognition Contract 1.30.11 / Contract de identificare

**Status: informational; family recognition only. Not an interoperability codec or normative file-format specification.**

## RO - Contractul pentru integratori

Scop: determinarea familiei probabile a unui fisier dupa semnatura si/sau extensie, fara conversie, decriptare, citirea tuturor entitatilor sau modificarea datelor. Identificarea nu certifica integritatea documentului.

Campuri JSON:

| Camp | Semnificatie |
|---|---|
| `file` | Numele local al fisierului; nu este trimis pe server |
| `size_bytes` | Dimensiunea in bytes |
| `expected_by_extension` | Familia presupusa doar din extensie, poate fi null |
| `identified` | Familia dedusa din semnatura sau extensie, poate fi null |
| `confidence` | `signature`, `legacy_signature`, `text_prefix`, `container_candidate`, `unverified_extension`, `unknown` |
| `evidence` | Explicatia verificabila pentru identificare |
| `mismatch` | Adevarat cand extensia cunoscuta contrazice semnatura recunoscuta |
| `valid_document` | Mereu `null`: citirea si validarea integrala NU sunt implementate |
| `tdb3_rc1` | Optional: verificare antet/superbloc CRC pentru formatul istoric 0.5.0 RC1 |

Prioritatea este semnatura, apoi prefixul text, apoi extensia; o extensie `.tsx` fara `TSSX\x00` ramane **unknown**. Pentru `.tdba`, `TDB1` inseamna candidat de container comun, nu dovada ca sectiunea TDBA este valida. Pentru `.tdocb` ZIP, prezenta unui membru denumit exact `FORMAT` este tot **candidat**; continutul sau nu se parseaza. Antetele TCAD/TCB/CGB/TXB identifica familiile; TCAD2.0 si CGB1 au acum verificari suplimentare LIMITATE, documentate separat, fara garantarea deschiderii native sau dreptului de scriere in format.

TDB3: verificarea RC1 calculeaza CRC32 pe corpul antetului si pe doua superblocuri alternative la offseturile 4096/8192; necesita versiune `1` si cel putin un superbloc cu semnatura/CRC corecte. **Nu** verifica arbori, payloaduri, tranzactii sau istoricul si **nu** suporta orice versiune viitoare.

### CLI Python (3.10+)

```text
python softcad_format_probe.py desen.tcb sector.txb
python softcad_format_probe.py --tdb3-header baza.tdb3
python softcad_format_probe.py --strict --json-output raport.json desen.tcb
python test_softcad_format_probe.py
python test_synthetic_vectors.py
```

`--strict`: exit code 2 pentru familie necunoscuta, extensie in contradictie cu semnatura ori CRC TDB3 RC1 invalid cand a fost solicitata inspectia. `--json-output` scrie **local** raportul; rezultatul continua sa apara si in stdout. Nu este validare de securitate/antivirus.

### JavaScript local / Node 20+

```text
node test_format_core.cjs
```

`softcad-format-core.js` expune `sniff(name, firstBytes, size)`, `tdb3RC1(firstBytes)`, `crc32(data)`, `inspectFile(File)` si `hasZipFormatMember(File)`. Interfata web ruleaza local, foloseste exclusiv File API si ofera un raport JSON doar la apasarea butonului. Nu exista incarcare de fisiere pe server.

### Vectorii sintetici

`vectors/manifest.json` defineste identitatea si amprenta SHA-256 a **22 de probe artificiale**. Unele probe sunt deliberat trunchiate, gresite ori cu CRC corupt. Niciuna nu este un document CAD/TDB valid, iar `valid_document` este mereu fals in manifest. Acestea testeaza contractul de recunoastere, NU interoperabilitatea reala.

## EN - Integration contract

Purpose: read-only, local file-family identification from public signatures and extensions. This is not an encoder, decoder, data validator, scanner, or format conformance certification.

Results report `file`, `size_bytes`, `expected_by_extension`, `identified`, `confidence`, `evidence`, `mismatch` and `valid_document:null`. `tdb3_rc1` is an optional, version-specific historical header/superblock CRC sanity result. An unknown `.tsx` file is **not** automatically a SoftCAD Shield container: only `TSSX\x00` confirms that family.

Confidence `signature` refers to byte prefix matching **only**. `container_candidate` means the outer container has the expected envelope (TDBA shared TDB1 or a ZIP central-directory `FORMAT` entry); it does not validate payloads. `unverified_extension` offers a navigation hint, not actual identification from file contents.

Run the Python and Node test commands above for 22 matching synthetic identity vectors. Never treat them as production format fixtures or normative file examples. For TDB3, version 1 + CRC checks cover the historical RC1 header and commit roots only; they do not prove that a database is usable.

## Licensing / scope

This independent recognizer is distributed under the accompanying Apache-2.0 license. The underlying SoftCAD formats and any commercial codecs have their own rights and release status. TSS Shield, internal keys, proprietary algorithms, the full TitanView application and the held Open Stack engines are not part of this kit. Owner-approved LGPL-3.0-or-later TVW graphics are documented separately.

TDB3 RC1 history verification is optional/read-only and bounded. ROOT PASS alone does not guarantee commit ancestry integrity. No Merkle certification.

## CGB1 subset observed in native engine / CGB1 - subset demonstrat

For the CGB1 v1 synthetic native fixture, the independent public probe checks a 140-byte header, section counts, ordered bounded offsets, and 44/40/24-byte Land/Person/Point spans ONLY when Parcel and Building counts are zero. Its positive result does not validate the record body, CRC, cadastral semantics or future versions. Nonzero Parcel/Building counts are **unsupported scope**, not an invalid-file verdict. See `CGB1_OBSERVED_SUBSET_RO_EN.md`.

## 1.30.16 TCB/TXB/TVW guardrail / 1.30.16 - verificări de frontieră

Regulă esențială: `DXB1` + extensia Autodesk `.dxb` este **ambiguu** și nu mai este raportat automat ca TXB. În `.txb`, `DXB1` este numai candidat istoric pentru citire; `.txbi` este index auxiliar separat. Pentru TCB, `TCB\x01` înseamnă doar semnătură de familie, fără citire de structură. TVW: doar text UTF-8 plauzibil, nu parser. Toate apar cu `format_authenticity=UNVERIFIED`, `normative_spec_covered=false`, `can_write=false`.

În CLI, `--strict` respinge acum cazurile cu semnătură absentă/conflict, coliziune `.dxb`, index auxiliar sau sursă TVW cu conținut binar. `--strict` cu prefix TCB/TXB corect poate ieși 0 **numai la nivel de identitate**, nicidecum validitate de fișier. Pentru o regulă automată care nu acceptă fișiere fără verificator normativ disponibil, folosiți `--require-normative` (în acest pachet întoarce 2 pentru TCB/TXB/TVW). Mai multe: `TCB_TXB_TVW_INTEGRATION_GATE_RO_EN.md`.

EN: Ambiguous `DXB1` under `.dxb` is never silently identified as TXB. Historical `DXB1` under `.txb` is a read-only candidate, `.txbi` is only an optional index, TCB detection is signature-only, and TVW UTF-8 plausibility is not grammar conformance. `--strict` is an envelope/identity gate, not validation. `--require-normative` explicitly fails pending true code-level normative verification.
