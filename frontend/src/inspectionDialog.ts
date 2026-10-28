// Match the native dialog to authorized selection after commit. Rendered details
// are gated separately, so private content disappears before this effect runs.
export function synchronizeInspectionDialog(dialog: Pick<HTMLDialogElement, 'open' | 'showModal' | 'close'> | null, visible: boolean) {
  if (!dialog) return;
  if (visible && !dialog.open) dialog.showModal();
  else if (!visible && dialog.open) dialog.close();
}
