# Formatele SoftCAD — kit public de identificare și verificări read-only

[**English**](README.md) · [Documentație oficială](https://softcad.ro/documentatie-dezvoltatori) · [Referința formatelor](https://softcad.ro/referinta-formate)

Acest depozit conține **cod independent de recunoaștere a familiilor de fișiere, exemple și teste**, extras din kitul public SoftCAD. Nu este un SDK de codecuri complete și nu conține motoare comerciale, Shield/TSX, chei, date reale sau unelte de scriere a documentelor.

**Conținut:** registrul de identitate 1.30.16, detectoare Python și JavaScript, subseturi observate TCAD 2.0 / CGB1, verificări limitate TDB3 RC1, compatibilitate conservatoare TCB/TXB/TVW și cazuri sintetice de test.

```bash
python softcad_format_probe.py vectors/header_only.tcb
python test_softcad_format_probe.py
node test_format_core.cjs
```

**Limite:** o semnătură recunoscută nu garantează fișier valid, compatibilitate completă, geometrie verificată ori interoperabilitate pentru scriere. TDB3 RC1 rămâne experimental. Vezi `README_RO_EN.md` și documentele specifice pentru delimitarea fiecărui format.

**Licență:** Apache-2.0 pentru materialele independente din acest depozit, cu atribuirea originală din `NOTICE.md`. Licența nu se extinde asupra codului comercial SoftCAD care nu este prezent aici. Proveniența fișierelor este în `SOURCE_PROVENANCE.json`.
