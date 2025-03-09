import pikepdf

# Create a sample owner-locked PDF (no user password)
with pikepdf.Pdf.new() as pdf:
    pdf.save('protected.pdf',
            encryption=pikepdf.Encryption(
                owner='testpass',
                allow_print=True,
                allow_modify_annotation=True,
                allow_assemble=True,
                allow_extract=True
            ))
print('Created test PDF: protected.pdf with owner password')