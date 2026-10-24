# SOFTCAD TCB/TXB/TVW Integration Gate — 1.30.16 (RO / EN)

**Status: INFORMATIVE, NOT A NORMATIVE SPECIFICATION.** No full TCB/TXB codecs, TVW parser, private engines or keys are distributed here.

## RO — Politica de compatibilitate

- **TCB** (`.tcb`): antet identificator `54 43 42 01` (`TCB\x01`). Detectarea antetului **nu** dovedește validitatea geometriei, lista de entități, reviziile, CRC-urile ori interoperabilitatea cu software-ul CAD.
- **TXB** (`.txb`): antet actual `TXB1` (`54 58 42 31`). Antetul istoric `DXB1` poate fi doar candidat la *citire legacy*, **fără permisiune de a scrie `.dxb`**. `.dxb` este extensie Autodesk. Fișierele cu antet DXB1 și nume `.dxb` sunt marcate **ambigue**, fără reclasificare automată în TXB; nu se modifică.
- **TXBI** (`.txbi`): index auxiliar opțional pentru TXB, *nu* desen independent. Nu este introdus ca format nativ separat.
- **TVW** (`.tvw`): limbaj declarativ aprobat pentru deschidere; stiva grafică `libtitangfx/path2` are aprobare LGPL separată. Detectorul poate verifica doar dacă fișierul este text UTF-8 plauzibil (maxim 64 KiB), **nu poate valida gramatica, rezolva componente sau executa TVW**. Un text arbitrar este doar `utf8_text_candidate`.
- **TSX**: fișierul `TSSX\x00` este container Shield privat; `.tsx` React/TypeScript nu este recunoscut automat ca Shield și nu face obiectul acestui gate.

Toate rezultatele au `format_authenticity=UNVERIFIED`, `can_write=false`, `normative_spec_covered=false`. Un pozitiv `signature_only` înseamnă *doar identificarea prefixului*. Un `source_size_limit` înseamnă **neinspectat**, nu valid ori invalid.

### Pași pentru închiderea contractelor normative

1. Importați **doar** codecurile publicabile (sursa canonică a citirii/scrierii TCB/TXB, cu proveniență și licență verificate) într-un mediu de audit, nu în ZIP-ul site-ului până la aprobare.
2. Generați fișiere **100% fictive** prin scriitorul oficial și redeschideți-le. Comparați semantica geometriei/layerelor/proprietăților, inclusiv round-trip DXF ↔ TXB; testați indexul `.txbi`, versiuni vechi DXB1 și erori de integritate.
3. Pentru TCB, extrageți contractul de versiune, antetul complet, secțiunile și checksumurile **direct din codecul canonic**, cu testare cross-platform.
4. Pentru TVW, publicarea gramaticii EBNF necesită parserul actual, exemple `.tvw` acceptate și respinse, API-ul componentelor și o matrice a țintelor Windows/Linux. Nu confundați parserul TVW cu motorul grafic LGPL.
5. Actualizați documentația numai când testele independente și verificarea juridică a distribuirii trec. Nu publicați fișiere reale de cadastru ori fragmente de cod comercial.

### Rulare locală

```
python softcad_format_probe.py --strict interop_vectors/tcb_signature.tcb
python test_tcb_txb_tvw_gate.py
node test_tcb_txb_tvw_gate.cjs
```

`softcad_format_probe.py` raportează și `interoperability_gate` pentru extensiile urmărite. Testele din `interop_vectors` sunt sintetice și **NU** reprezintă fișiere TCB/TXB/TVW valide. Inspectorul browser rămâne local; niciun fișier nu este încărcat în rețea.

## EN — Compatibility and publication boundaries

**TCB:** `TCB\x01` is a file-family prefix only, not a binary specification or evidence of a valid CAD document. **TXB:** `TXB1` is the active identity; `DXB1` is historical *read-only candidate* under `.txb`. Autodesk `.dxb` must never be silently treated as SoftCAD TXB. `.txbi` is an auxiliary index only. **TVW:** `.tvw` source may be screened for bounded UTF-8 text plausibility, but not parsed, compiled, rendered or grammar-validated by this kit. `libtitangfx/path2` graphics LGPL approval is separate from declaring the declarative parser specification complete.

Before claiming interoperability, independently audit the approved canonical codecs/parser with real **synthetic** writer-generated fixtures, version and corruption cases, cross-platform read/write semantics and rights to redistribute. No commercial/private components or complete file grammar are contained in this kit.
