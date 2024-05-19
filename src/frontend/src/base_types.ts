export enum BinaryScale {
  b = "Bytes",
  k = "Kilobytes",
  M = "Megabytes",
  G = "Gigabytes",
  T = "Terabytes",
  P = "Petabytes",
  E = "Exabytes",
}

export class BinarySizedValue {
  value: number;
  scale: BinaryScale;

  constructor(value: number = 0, scale: BinaryScale = BinaryScale.G) {
    this.value = value;
    this.scale = scale;
  }
}

export class ExceptionSchema {
  readonly status: number;
  readonly msg: string;

  constructor(status: number = 400, msg: string = 'There was a problem') {
    this.status = status;
    this.msg = msg
  }
}

export class EntityNotFoundException extends ExceptionSchema {}
export class EntityInvariantException extends ExceptionSchema {}

export abstract class Entity {
  readonly uid: string = "";
  name: string = "";
}

export abstract class ModifiableEntity<T extends Entity> {
  name: string;

  protected constructor(original: T) {
    this.name = original.name;
  }
}

export abstract class CreatableEntity {
  name: string = "";
}
