export enum BinaryScale {
  b = "Bytes",
  k = "Kilobytes",
  M = "Megabytes",
  G = "Gigabytes",
  T = "Terabytes",
  P = "Petabytes",
  E = "Exabytes"
}

export interface BinarySizedValue {
  value: number,
  scale: BinaryScale
}

export enum DialogKind {
    create,
    modify,
    remove
}
