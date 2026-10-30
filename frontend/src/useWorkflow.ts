import { useEffect, useState, useSyncExternalStore } from 'react';
import type { AccessSession } from './access';
import { WorkflowController } from './workflowController';

export function useWorkflow(access: AccessSession) {
  const [controller] = useState(() => new WorkflowController(access));
  const snapshot = useSyncExternalStore(controller.subscribe, controller.snapshot, controller.snapshot);
  useEffect(() => {
    controller.start();
    return controller.stop;
  }, [controller]);
  return { ...snapshot, mutate: controller.mutate, submitPhoto: controller.submitPhoto, refresh: controller.refresh, inspect: controller.inspect };
}
