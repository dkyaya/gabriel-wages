# Downstream source-packaging policy

The next task must not create a full uncompressed staging copy. It must stream directly from existing canonical source roots into bounded compressed split volumes, write and checksum each volume independently, validate reconstruction before any deletion, keep no more than one bounded volume plus compression overhead locally where possible, assume no external storage device, and never delete original sources without package verification, transfer, and explicit user approval.
