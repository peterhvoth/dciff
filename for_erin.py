from pathlib import Path
import shutil
import os 

rundef = [{'dest' : Path('/home/peterhvoth/DCIFF Dropbox/DCIFF_Shared/images'), 'types' : ['.jpg', '.png', '.tif', '.tiff']}, 
          {'dest' : Path('/home/peterhvoth/DCIFF Dropbox/DCIFF_Shared/trailers'), 'types' : ['.mp4', '.mov']}]

srcdir = Path('/home/peterhvoth/DCIFF Dropbox/DCIFF_Current_Year/DCIFF_2020_FILMS')
for item in rundef:
    for i in srcdir.rglob('*'):
        dest = item['dest'].joinpath('/'.join(i.parts[7:]))
        if i.suffix.lower() in item['types']:
            if not dest.parent.exists():
                if not dest.parent.parent.exists():
                    os.mkdir(str(dest.parent.parent))
                os.mkdir(str(dest.parent))
            shutil.copy(str(i), str(dest))
            
        