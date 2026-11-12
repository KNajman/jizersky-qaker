"""Git clean filter pro obrazky/nakresy/*.svg: do repa jde SVG bez vrstvy „originál“ (obrázek z ČHS), lokálně zůstává.
Nastavení (jednou v každém klonu): git config filter.nakres.clean "python3 skripty/bez_originalu.py" """
import re, sys
s = sys.stdin.buffer.read().decode('utf-8')
s = re.sub(r'<g\b[^>]*inkscape:label="originál"[^>]*>.*?</g>\s*', '', s, flags=re.S)
sys.stdout.buffer.write(s.encode('utf-8'))
