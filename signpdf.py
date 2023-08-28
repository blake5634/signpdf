#!/usr/bin/python3

import os
import time
import argparse
import tempfile
import PyPDF2
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape

# future: to support decrypting sigature file
#from PIL import Image


# for gui clicking
import matplotlib.pyplot as plt
import matplotlib.image as img
import numpy as np
import PIL.Image
from scipy.ndimage import rotate


import time

YOUR_FAV_SIGNATURE_IMAGE = '/home/blake/templates/signature.png'

parser = argparse.ArgumentParser(">signpdf.py")
# future - store encrypted signature image
#parser.add_argument('key', help='key to decript your signature file')
parser.add_argument("pdf", help="The pdf file to annotate")
# signature is now optional- a default is available
parser.add_argument("signature", nargs='?',
        help="(optional)The signature file (png, jpg)")
parser.add_argument("--date", action='store_true',
        help='enable clicking a second location for adding signature date.')
parser.add_argument("--output", nargs='?',
        help="Output file. Defaults to input filename plus '_signed_XX'.pdf  (XX = initials)")
parser.add_argument("--pageno", help="Which page to apply the signature (default= 1).")
parser.add_argument("--text", action='store_true', help='Add text to the PDF instead of a signature')

def tellme(s):
    print(s)
    plt.title(s, fontsize=16)
    plt.draw()

initials = 'BH'

screenscale = 1.5   # matplotlib display inches over paper size inches
positscale  = 1.0
pdfdpi = 72.0       # PDF dots per inch

def co_xform(p1,mode):   # assumes paper = US Letter
    if mode == 'portrait':
        pageheightIn = 11.0
    else:
        pageheightIn = 8.5
    xfudge = 0
    yfudge = 5   # seems better
    x1 = p1[0] + xfudge
    y1 = p1[1] + yfudge
    x2 = int((0.5+x1)*positscale)
    y2 = int((0.5+ pageheightIn*pdfdpi - y1)*positscale)
    return [x2,y2]

def sigbox(filename):
    # compute signature size in pixels
    #  TODO: open the signature file and figure out its height & width
    #    (but do we know the dpi??)
    sx = 2.0  # in    ###   hard coded for now
    sy = 0.625 # in
    x = int(0.5+pdfdpi*sx)
    y = int(0.5+pdfdpi*sy)
    return [x,y]

def sig_descender_offset():  # vertical shift to allow descenders below click pt
    #
    #  future: figure this value out by image analysis of signature!!
    #
    desc_in = 0.250*positscale  #inches below sig line (click pt)
    return desc_in * pdfdpi

def get_locations(args,sig_page,sigtext):
    # with thanks to:
    #https://matplotlib.org/3.0.0/_downloads/ginput_manual_clabel_sgskip.py
    #
    #plt.clf()
    writer = PyPDF2.PdfFileWriter()

    # create temp file and convert to png for intractive location clicking
    pdfFileName = args.pdf
    uniquetmpName = 'tmp1pageExr48csdH5ru'
    writer.addPage(sig_page)
    with open(uniquetmpName+'.pdf', 'wb') as fh:
        writer.write(fh)
    fh.close()


    ###  generate a 1-page PDF of the sig page for preview/clicking
    ##outputPDFname = args.output or "{}_signed{}".format(os.path.splitext(args.pdf))
    ##cmd = 'pdftk {:} cat {:} output {:}'.format(pdfFileName, sig_page, outputPDFname )
        ######       **** exectute command ... then:
    ##print('Executing: ', cmd)
    ##os.system(cmd)
    ## maybe no longer necessary to get 72dpi????
    cmd = 'convert -density 288 {:}.pdf -resize 25% {:}.png'.format(uniquetmpName, uniquetmpName)  # should give 72 dpi
    print('Executing: ', cmd)
    os.system(cmd)

    page_img = img.imread(uniquetmpName+'.png')
    r,c,d = page_img.shape
    if r>c:
        w = screenscale*8.5
        h = screenscale*11.0
        orientationmode = 'portrait'
    else:
        w = screenscale*11.0   # landscape
        h = screenscale*8.5
        orientationmode = 'landscape'
    fig, ax = plt.subplots(figsize=(w,h))

    ax.imshow(page_img)
    plt.setp(plt.gca(), autoscale_on=False)

    if args.text:
        click1target = '"'+sigtext+'"'
    else:
        click1target = 'signature'
    if args.date:
        tellme('Please click locations of {:} and date ... then close the preview.'.format(click1target))
    else:
        tellme('Please click location of {:} ... then close the preview.'.format(click1target))

    #plt.waitforbuttonpress()
    if args.date:
        npts = 2
    else:
        npts = 1

    x = np.asarray(plt.ginput(npts,timeout=-1))
    print('1:',x)
    ptsig = x[0]
    plt.text(ptsig[1],ptsig[0],'x',color='b')

    ptd = None  # image point for date
    if args.date:
        ptd = x[1]
        plt.text(ptd[1],ptd[0],'x',color='g')

    if orientationmode == 'landscape':
        for i,p in enumerate(x):  # swap x,y dimensions
            t = x[i][0]
            x[i][0] = x[i][1]
            x[i][1] = t

    print('2:',x)

    plt.show()


    #print('You clicked (a): ', pt)
    # get int typed PDF coordinates of sig and date
    pdf_pt_sig = co_xform(ptsig,orientationmode)
    pdf_pt_date = None
    if ptd is not None:
        pdf_pt_date = co_xform(ptd,orientationmode)

    print('Sig  location:  {:}'.format(pdf_pt_sig))
    if ptd is not None:
        print('Date location:  {:}'.format(pdf_pt_date))

    # cleanup
    #os.system('rm {:}'.format(uniquetmpName+'.png'))
    #os.system('rm {:}'.format(uniquetmpName+'.pdf'))
    # package results
    locs = [pdf_pt_sig, pdf_pt_date]
    return locs, orientationmode

def swap(a,b):
    return b,a

def get_sig_image_info(args):
    #
    #  TODO: open image file, read it in and DECRYPT it.
    #        c.drawImage is SUPPOSED to work with a PIL formatted
    #        image in memory but seems not to.
    #
    #   for now only file name is returned (no encryption)
    #
    if args.signature is not None:
        img_file_path = args.signature
    else:
        ###   easier to use if repeating one sig file
        img_file_path = YOUR_FAV_SIGNATURE_IMAGE
    dims = sigbox(img_file_path)
    print('Signature I will use is:', img_file_path, dims)
    return img_file_path, dims

def _get_tmp_filename(suffix=".pdf"):
    with tempfile.NamedTemporaryFile(suffix=".pdf") as fh:
        return fh.name

def sign_pdf(args):
    try:
        int(args.pageno)
        # correct the page number for list index usage
        page_num = int(args.pageno) - 1
    except:
        page_num = 1 -1  # default is page 1

    print(' We are going to sign page: ', page_num+1)

    fnameroot = os.path.splitext(args.pdf)[0]
    fnameext  = os.path.splitext(args.pdf)[1]
    output_filename = args.output or f"{fnameroot}_signed_{initials}{fnameext}"

    #
    #   input the text in text-mode
    #

    sigtext = None
    if args.text:
        sigtext = input('Please enter the desired text:')

    pdf_fh = open(args.pdf, 'rb')
    sig_tmp_fh = None

    pdf = PyPDF2.PdfFileReader(pdf_fh)
    writer = PyPDF2.PdfFileWriter()
    pageImage_tmp_filename = None

    hashkey = 'c9010ea5923339f4214c6a6eb2547b1a34a750c7ccd42980b678d61dfc9e33ac'
    args.key = hashkey
    sig_img_name, dims = get_sig_image_info(args)

    for i in range(0, pdf.getNumPages()):
        page = pdf.getPage(i)

        if i == page_num:  # now we are on the signature page
            # Create PDF for signature
            pageImage_tmp_filename = _get_tmp_filename()
            # get user to click locations
            locs, orientationmode = get_locations(args,page,sigtext)
            (x1,y1) = locs[0]  # sig location
            yshift = sig_descender_offset()
            if args.date:
                (x2,y2) = locs[1]  # date location
            # load in the page for marking
            c = canvas.Canvas(pageImage_tmp_filename, pagesize=page.cropBox)
            [width , height] = dims # of signature
            c.drawImage(args.signature, x1, y1, width, height, mask='auto')
            #if orientationmode=='portrait':
            drx1 = x1
            dry1 = y1
            #else:
                #drx1 = y1  # swap for landscape mode
                #dry1 = x1
            if args.text:  # we are placing text instead of the signature
                c.drawString(drx1,dry1, sigtext)
            else:
                print('drawing sig img: ', drx1, dry1, -yshift)
                c.drawImage(sig_img_name, drx1, dry1-yshift, width, height, mask='auto')
            if args.date:
                #if orientationmode=='portrait':
                drx2 = x2
                dry2 = y2
                #else:
                    #drx2 = y2  # swap for landscape mode
                    #dry2 = x2

                print('drawing date: ', drx2, dry2)

                c.drawString(drx2,dry2, datetime.datetime.now().strftime("%d-%b-%Y"))

            #c.showPage()
            c.save()

            # Merge PDF in to original page
            sig_tmp_fh = open(pageImage_tmp_filename, 'rb')
            sig_tmp_pdf = PyPDF2.PdfFileReader(sig_tmp_fh)
            sig_page = sig_tmp_pdf.getPage(0)
            sig_page.mediaBox = page.mediaBox
            page.mergePage(sig_page)

        writer.addPage(page)

    with open(output_filename, 'wb') as fh:
        writer.write(fh)

    for handle in [pdf_fh, sig_tmp_fh]:
        if handle:
            handle.close()
    if pageImage_tmp_filename:
        os.remove(pageImage_tmp_filename)

def main():

    sign_pdf(parser.parse_args())

if __name__ == "__main__":
    main()
