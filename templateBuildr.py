from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Transaction,
    ViewDrafting,
    ElementId,
    ElementCategoryFilter,
    BuiltInCategory,
    ElementTransformUtils,
    XYZ,
    Transform
)
from pyrevit import revit, DB, forms
import Autodesk.Revit.DB as DB
import clr
import os

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
    app = revit.app  # Get the Revit application
    if not os.path.exists(master_path):
        forms.alert(f"Master document not found at: {master_path}", title="Error", warn_icon=True)
        return None
    # Open the master document
    try:
        master_doc = app.OpenDocumentFile(master_path)
        return master_doc
    except Exception as e:
        forms.alert(f"Failed to open master document.\nError: {e}", title="Error", warn_icon=True)
        return None

# Function to delete all elements in a drafting view
def delete_elements_in_view(doc, view):
    # Get all elements visible in the view
    collector = FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType().ToElements()
    # Optionally, filter out certain categories if needed
    # For example, to exclude annotations:
    # collector = [e for e in collector if not e.Category or e.Category.CategoryType != DB.CategoryType.Annotation]
    ids_to_delete = [e.Id for e in collector]
    if ids_to_delete:
        DB.ElementTransformUtils.DeleteElements(doc, ids_to_delete)

# Function to copy elements from master view to current view
def copy_elements_from_master(doc, master_doc, master_view, current_view):
    # Get all elements in the master view
    master_elements = FilteredElementCollector(master_doc, master_view.Id).WhereElementIsNotElementType().ToElements()
    # Prepare list of ElementIds to copy
    elements_to_copy = [e.Id for e in master_elements]
    # Define the destination view
    dest_view_id = current_view.Id
    # Perform the copy operation
    try:
        copied_elements = ElementTransformUtils.CopyElements(
            master_doc,
            elements_to_copy,
            doc,
            Transform.Identity,
            DB.CopyPasteOptions()
        )
        # Optionally, move elements to the destination view by setting their view-specific parameters
        for copied_elem_id in copied_elements:
            copied_elem = doc.GetElement(copied_elem_id)
            # Example: Assign to current view if applicable
            # Note: This depends on element type and whether they are view-specific
    except Exception as e:
        forms.alert(f"Failed to copy elements from master view '{master_view.Name}' to current view '{current_view.Name}'.\nError: {e}", title="Error", warn_icon=True)

# Function to compare and update drafting views
def update_drafting_views_from_master(master_doc, current_doc):
    master_views_dict = get_drafting_views_dict(master_doc)
    current_views_dict = get_drafting_views_dict(current_doc)

    with Transaction(current_doc, "Update Drafting Views from Master") as trans:
        trans.Start()
        for view_name, master_view in master_views_dict.items():
            if view_name in current_views_dict:
                current_view = current_views_dict[view_name]
                # Delete existing elements in the current view
                delete_elements_in_view(current_doc, current_view)
                # Copy elements from master view to current view
                copy_elements_from_master(current_doc, master_doc, master_view, current_view)
                print(f"Drafting view '{view_name}' has been updated from the master model.")
            else:
                # Optionally, create the view in current_doc if it doesn't exist
                # This requires duplicating the view from master_doc to current_doc
                forms.alert(f"Drafting view '{view_name}' does not exist in the current document.", title="Info", warn_icon=False)
        trans.Commit()

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

    # Ensure master_doc and current_doc are not the same
    if master_doc.Id == current_doc.Id:
        forms.alert("Master document and current document are the same.", title="Error", warn_icon=True)
        return

    update_drafting_views_from_master(master_doc, current_doc)

    # Optionally, close the master document if it was opened by the script
    try:
        master_doc.Close(False)  # False to not save changes
    except Exception as e:
        print(f"Could not close master document: {e}")

# Call the main function
if __name__ == "__main__":
    main()
