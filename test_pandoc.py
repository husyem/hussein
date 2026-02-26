import pypandoc

html1 = '<p>Test <span class="math inline">\\( E=mc^2 \\)</span></p>'
html2 = '<p>Test <span class="math display">\\[ E=mc^2 \\]</span></p>'

print(pypandoc.convert_text(html1, to='markdown', format='html'))
print(pypandoc.convert_text(html2, to='markdown', format='html'))
