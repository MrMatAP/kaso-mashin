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

export enum ExceptionKind {
  KASOMASHIN = "KasoMashinException",
  ENTITYNOTFOUND = "EntityNotFoundException",
  ENTITYINVARIANT = "EntityInvariantException",
}

export class KasoMashinException {
  readonly kind: ExceptionKind;
  readonly status: number;
  readonly msg: string;

  constructor(
    status: number = 400,
    msg: string = "There was a problem",
    kind: ExceptionKind = ExceptionKind.KASOMASHIN,
  ) {
    this.status = status;
    this.msg = msg;
    this.kind = kind;
  }

  static fromError(error: any) {
    if ("body" in error && "kind" in error.body) {
      switch (error.body.kind) {
        case ExceptionKind.KASOMASHIN:
          return new KasoMashinException(error.body.status, error.body.kind);
        case ExceptionKind.ENTITYNOTFOUND:
          return new EntityNotFoundException(error.body.status, error.body.kind);
        case ExceptionKind.ENTITYINVARIANT:
          return new EntityInvariantException(error.body.status, error.body.kind);
      }
    }
    return new this(500, error.message);
  }
}

export class EntityNotFoundException extends KasoMashinException {
  constructor(status: number, msg: string) {
    super(status, msg, ExceptionKind.ENTITYNOTFOUND);
  }
}

export class EntityInvariantException extends KasoMashinException {
  constructor(status: number, msg: string) {
    super(status, msg, ExceptionKind.ENTITYINVARIANT);
  }
}

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

export class UIEntitySelectOptions {
  uid: string;
  name: string;

  constructor(uid: string, name: string) {
    this.uid = uid;
    this.name = name;
  }
}
