from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Transaction,
    ViewDrafting,
    ElementId,
    ElementTransformUtils,
    Transform,
    OpenOptions,
    ModelPathUtils,
    FilePath,
    CopyPasteOptions,
    DetachFromCentralOption
)
from pyrevit import revit, DB, forms
import Autodesk.Revit.DB as DB
import clr
clr.AddReference("System")
from System.Collections.Generic import List, Dictionary
import os

ui = __revit__.ActiveUIDocument

# Function to get a dictionary of drafting view names and their elements
def get_drafting_views_dict(doc):
    drafting_views_dict = {}
    collector = FilteredElementCollector(doc).OfClass(ViewDrafting).WhereElementIsNotElementType()
    for view in collector:
        if not view.IsTemplate:
            drafting_views_dict[view.Name] = view
    return drafting_views_dict

# Function to load the master document
def load_master_document(master_path):
    app = __revit__.Application
    if not os.path.exists(master_path):
        forms.alert(
            "Master document not found at: {}".format(master_path),
            title="Error",
            warn_icon=True
        )
        return None
    try:
        model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(master_path)
        open_options = DB.OpenOptions()
        # Set detach from central option if necessary
        open_options.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets
        master_doc = app.OpenDocumentFile(model_path, open_options)
        return master_doc
    except Exception as e:
        forms.alert(
            "Failed to open master document.\nError: {}".format(e),
            title="Error",
            warn_icon=True
        )
        return None

# Function to delete all elements in a drafting view
def delete_elements_in_view(doc, view):
    # Get all elements visible in the view
    collector = FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType().ToElements()
    # Convert to .NET List[ElementId]
    ids_to_delete = List[ElementId]([e.Id for e in collector])
    if ids_to_delete.Count > 0:
        doc.Delete(ids_to_delete)

# Function to copy elements from master view to current view
def copy_elements_from_master(doc, master_doc, master_view, current_view):
    from System.Collections.Generic import List, Dictionary
    # Get all elements in the master view
    master_element_ids = FilteredElementCollector(master_doc, master_view.Id) \
        .WhereElementIsNotElementType().ToElementIds()
    # Convert to .NET ICollection<ElementId>
    elements_to_copy = List[ElementId](master_element_ids)
    if elements_to_copy.Count == 0:
        print("No elements to copy from master view '{}'.".format(master_view.Name))
        return
    # Create a mapping between the source view and destination view
    view_mapping = Dictionary[ElementId, ElementId]()
    view_mapping[master_view.Id] = current_view.Id
    # Perform the copy operation
    copy_options = CopyPasteOptions()
    try:
        copied_elements = ElementTransformUtils.CopyElements(
            master_doc,
            elements_to_copy,
            doc,
            view_mapping,
            Transform.Identity,
            copy_options
        )
        print("Successfully copied elements from '{}' to '{}'.".format(master_view.Name, current_view.Name))
    except Exception as e:
        forms.alert(
            "Failed to copy elements from master view '{}' to current view '{}'.\nError: {}".format(
                master_view.Name, current_view.Name, e
            ),
            title="Error",
            warn_icon=True
        )

# Function to compare and update drafting views
def update_drafting_views_from_master(master_doc, current_doc):
    master_views_dict = get_drafting_views_dict(master_doc)
    current_views_dict = get_drafting_views_dict(current_doc)

    for view_name, master_view in master_views_dict.items():
        if view_name in current_views_dict:
            current_view = current_views_dict[view_name]
            try:
                # Start transactions in both documents
                trans_current = Transaction(current_doc, "Update Drafting View '{}'".format(view_name))
                trans_master = Transaction(master_doc, "Prepare Elements for Copy '{}'".format(view_name))

                trans_current.Start()
                trans_master.Start()

                # Delete existing elements in the current view
                delete_elements_in_view(current_doc, current_view)
                # Copy elements from master view to current view
                copy_elements_from_master(current_doc, master_doc, master_view, current_view)

                trans_current.Commit()
                trans_master.Commit()

                print("Drafting view '{}' has been updated from the master model.".format(view_name))
            except Exception as e:
                trans_current.RollBack()
                trans_master.RollBack()
                forms.alert(
                    "Failed to update drafting view '{}'.\nError: {}".format(view_name, e),
                    title="Error",
                    warn_icon=True
                )
        else:
            forms.alert(
                "Drafting view '{}' does not exist in the current document.".format(view_name),
                title="Info",
                warn_icon=False
            )

# Main function
def main():
    # Prompt user to select the master document
    master_path = forms.pick_file(file_ext='rvt', title="Select the Master Revit Document")
    if not master_path:
        forms.alert("No master document selected.", title="Cancelled", warn_icon=True)
        return

    master_doc = load_master_document(master_path)
    if not master_doc:
        return

    current_doc = revit.doc  # This is your current project document

    # Debugging: Print document paths
    print("Current Document Path: {}".format(current_doc.PathName))
    print("Master Document Path: {}".format(master_doc.PathName))

    # Ensure master_doc and current_doc are not the same
    if master_doc.PathName == current_doc.PathName:
        forms.alert("Master document and current document are the same.", title="Error", warn_icon=True)
        return

    update_drafting_views_from_master(master_doc, current_doc)

    # Close the master document if it was opened by the script
    try:
        master_doc.Close(False)  # False to not save changes
    except Exception as e:
        print("Could not close master document: {}".format(e))


# Call the main function
if __name__ == "__main__":
    main()
