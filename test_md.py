import markdownify
import pypandoc

html_str = '<p>Test <b>bold</b> and math: $E=mc^2$</p>'
md = markdownify.markdownify(html_str)
print("Markdownify output:", repr(md))

# Now send this markdown to pypandoc to create docx
pypandoc.convert_text(md, to='docx', format='markdown+tex_math_dollars', outputfile='out.docx')

print("Docx generated!")
