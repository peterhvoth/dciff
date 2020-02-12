from pathlib import Path
import shutil
import os 

tmp = []
out = Path('/home/peterhvoth/Dropbox/DCIFF_Shared/_images')
p = Path('/home/peterhvoth/Dropbox/DCIFF_Shared/DCIFF_2020_FILMS')
for i in p.rglob('*'):
    dest = out.joinpath('/'.join(i.parts[7:]))
    if i.suffix.lower() in ['.jpg', '.png', '.tif', '.tiff']:
        if not dest.parent.exists():
            if not dest.parent.parent.exists():
                os.mkdir(str(dest.parent.parent))
            os.mkdir(str(dest.parent))
        shutil.copy(str(i), str(dest))
        
        