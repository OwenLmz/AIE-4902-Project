# Web Sample Image Sources

These images are public web samples used only for sanity-checking the YOLO + ROI + state-machine pipeline. They are not a formal accuracy benchmark for the target school library.

## Selected test images

| Local file | Source page | Direct image URL | Test purpose |
|---|---|---|---|
| `images/web_test/WEB-S3_free_empty_room.jpg` | University of Delaware Library, Museums and Press - Study Spaces | `https://library.udel.edu/ourspaces/wp-content/uploads/sites/32/2018/10/20090508_0192-405x270.jpg` | Empty seat/table ROI -> `free` |
| `images/web_test/WEB-S4_suspected_backpack.jpg` | University of Delaware Library, Museums and Press - Study Spaces | `https://library.udel.edu/ourspaces/wp-content/uploads/sites/32/2018/10/IMG_1901-405x270.jpg` | Backpack in ROI, no person in ROI -> `suspected` |
| `images/web_test/WEB-S5_occupied_student.jpg` | University of Delaware Library, Museums and Press - Study Spaces | `https://library.udel.edu/ourspaces/wp-content/uploads/sites/32/2018/10/IMG_6552-405x270.jpg` | Person and objects in ROI -> `occupied` |

## Other downloaded candidates

| Local file | Source page | Direct image URL |
|---|---|---|
| `images/web_samples/WEB-02_occupied_students.jpg` | University of Delaware Library, Museums and Press - Strategic Directions Overview | `https://library.udel.edu/strategicdirections/wp-content/uploads/sites/18/2017/09/05-Overview-1.jpg` |
| `images/web_samples/WEB-04_research_scholarship.jpg` | University of Delaware Library, Museums and Press - Research, Scholarship and Discovery | `https://library.udel.edu/strategicdirections/wp-content/uploads/sites/18/2017/09/02-ResearchScholarship.jpg` |

