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

export enum DialogKind {
  create,
  modify,
  remove,
}
