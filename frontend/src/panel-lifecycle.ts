export function shouldStartInitialLoad(
  initialLoadStarted: boolean,
  hassChanged: boolean,
  hassAvailable: boolean,
): boolean {
  return !initialLoadStarted && hassChanged && hassAvailable;
}
