"""
widget manager to register your widgets with bqt

- parent widget to blender window (blender_widget)
- keep widget in front of Blender window only, even when bqt is not wrapped in qt
"""
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
import logging


__widgets = []
__excluded_widgets = []


class WidgetData():
    def __init__(self, widget, visible):
        self.widget = widget
        self.visible = visible


def register(widget, exclude=None, parent=True, manage=True):
    """
    parent widget to blender window
    Args:
        widget: child widget to parent
        parent: if True, parent the widget to the blender window
        exclude: widgets to exclude from being parented to the blender window
        manage: if True, manage the visibility of the widget
    """
    exclude = exclude or []

    if not widget:
        logging.warning("bqt: widget is None, skipping widget registration")
        return

    parent_widget = QApplication.instance().blender_widget
    if widget == parent_widget:
        return

    if widget in exclude:
        logging.warning("bqt: widget is in exclude list, skipping widget registration")
        return

    # parent to blender window
    if parent:
        vis = widget.isVisible()
        widget.setParent(parent_widget, Qt.Window)  # default set flag to window
        widget.setVisible(vis)  # parenting hides the widget, restore visibility

    # save widget so we can manage the focus and visibility
    if manage:
        data = WidgetData(widget, widget.isVisible())  # todo can we init vis state to false?
        __widgets.append(data)


def iter_widget_data():
    """iterate over all registered widgets, remove widgets that have been removed"""
    cleanup = []
    for widget_data in __widgets:
        if not widget_data.widget:
            cleanup.append(widget_data)
            continue
        yield widget_data
    for widget_data in cleanup:
        __widgets.remove(widget_data)


def _blender_window_change(hwnd: int):
    """
    hide widgets when blender is not focussed,
    keep widgets in front of the Blender window when Blender is focussed
    run when changing between a blender & non-blender window
    """
    focussed_on_a_blender_window = hwnd != 0  # 0 for windows not created by blender

    for widget_data in iter_widget_data():
        widget = widget_data.widget

        if focussed_on_a_blender_window:

            # add top flag, ensure the widget stays in front of the blender window
            widget.setWindowFlags(widget.windowFlags() | Qt.WindowStaysOnTopHint)

            # restore visibility state of the widget
            if widget_data.visible:
                widget.show()

        else:  # non-blender window
            # save visibility state of the widget
            widget_data.visible = widget.isVisible()

            # remove top flag, allow the widget to be hidden behind the blender window
            # self.blender_widget2.setWindowFlags(self.blender_widget2.windowFlags() & ~Qt.WindowStaysOnTopHint)
            widget.hide()  # todo since we hide do we need to remove flag?

    # todo right now widgets stay in front of other blender windows,
    #  e.g. the preferences window, ideally we handle this


def _orphan_toplevel_widgets():
    return [widget for widget in QApplication.instance().topLevelWidgets() if
            not widget.parent()
            and widget not in __widgets
            and widget not in __excluded_widgets]


def parent_orphan_widgets(exclude=None):
    """Find and parent orphan widgets to the blender widget"""
    exclude = exclude or []
    __excluded_widgets.extend(exclude)
    for widget in _orphan_toplevel_widgets():
        register(widget, exclude=exclude)