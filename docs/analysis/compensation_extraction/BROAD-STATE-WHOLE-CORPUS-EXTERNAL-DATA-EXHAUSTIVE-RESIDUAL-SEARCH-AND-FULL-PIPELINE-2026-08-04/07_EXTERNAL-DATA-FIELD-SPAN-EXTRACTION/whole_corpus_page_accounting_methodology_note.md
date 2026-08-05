# Whole-corpus page accounting methodology

All locally retained PDF files under canonical artifact and original corpus roots were SHA-256 hashed. Identical hashes count once; distinct versions count separately. Native pages were counted directly from physical PDFs using pypdf. HTML and structured sources have no native page count. OCR-later/image-only PDFs contribute native pages when readable page metadata exists. Storage-held and unsearched sources are excluded. Page count measures scale, not evidentiary quality.
