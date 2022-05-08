from pikepdf import Pdf, PdfImage
import io
import zipfile
import os
import time


def extract(page, **kwargs):
    verbose = kwargs.get("verbose", False)
    zipFile = kwargs.get("zipFile")
    done = kwargs.get("done")
    if verbose:
        print(f"Page : {page.label}")
    for j, (k,im) in enumerate(page.images.items()):
        pageNumber = page.index + 1
        if verbose:
            print(pageNumber, j)
        if im.objgen in done:
            if verbose:
                print(f"{pageNumber}-{j} already extracted")
            continue
        with io.BytesIO() as f:
            mask = getattr(im.stream_dict, "SMask", None)
            
            pdfimage = PdfImage(im)
            if mask is None:
                extension = pdfimage.extract_to(stream=f)
                name = f'{pageNumber}-{j}{extension}'
                if verbose:
                    print(name)
                zipFile.writestr(name, f.getvalue())
            else:
                maskImage = PdfImage(mask)
                img_PIL = pdfimage.as_pil_image()
                mask_PIL = maskImage.as_pil_image()
                colors = mask_PIL.getcolors()
                if colors is None or len(colors) == 1:
                    extension = pdfimage.extract_to(stream=f)
                    name = f'{pageNumber}-{j}{extension}'
                    if verbose:
                        print(name)
                    zipFile.writestr(name, f.getvalue())
                else:
                    img_PIL = img_PIL.convert("RGB")
                    mask_PIL = mask_PIL.convert("L")
                    img_PIL.putalpha(mask_PIL)
                    img_PIL.save(f, format="png")
                    name = f'{pageNumber}-{j}.png'
                    if verbose:
                        print(name)
                    zipFile.writestr(name, f.getvalue())
                    
                img_PIL.close()
                mask_PIL.close()
            
            done.append(im.objgen)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", type=str)
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
    parser.add_argument("-o", "--outputfile", type=str)
    parser.add_argument("-z", "--compressionlevel", type=int, default=-1)
    args = parser.parse_args()
    
    try:
        file = Pdf.open(args.inputfile)
        done = []
        if args.outputfile is None:
            args.outputfile = os.path.splitext(args.inputfile)[0] + ".zip"
        start = time.perf_counter()
        compressionMethod = zipfile.ZIP_DEFLATED
        if args.compressionlevel == -1:
            compressionMethod = zipfile.ZIP_STORED

        with zipfile.ZipFile(args.outputfile, "w", compressionMethod, False, compresslevel=args.compressionlevel) as zip_file:
            for i, page in enumerate(file.pages):
                extract(page, zipFile = zip_file, done=done, verbose=args.verbose)
                print(f"{i/len(file.pages):.0%}", end="\r")
        # if verbose:
        processTime = time.perf_counter()-start
        print(f"Extraction done in {processTime}")
    
    except FileNotFoundError:
        print("File not found !")