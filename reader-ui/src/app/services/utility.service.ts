import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class UtilityService {

  constructor() { }

  isDefined(input: any) {
    return !(input === undefined || input === null);
  }

  /**
   * Description: Function to check if input is undefined.
   *
   * @returns
   */
  isUndefined(input: any) {
    return (input === undefined || input === null);
  }

  isArrayDefined(input: any[]) {
    return (this.isDefined(input) && input.length > 0);
  }

  /**
   * Description: Checks if Input is empty
   * @returns
   */
  isEmpty(input: string) {
    if (this.isUndefined(input)) {
      return true;
    }
    return (input.trim() === '');
  }
}
