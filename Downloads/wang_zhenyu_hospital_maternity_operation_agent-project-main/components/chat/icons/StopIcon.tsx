export interface IconProps {
  size?: number;
  className?: string;
}

export const StopIcon = ({ size = 16, className }: IconProps) => {
  return (
    <svg
      height={size}
      viewBox="0 0 16 16"
      width={size}
      className={className}
      style={{ color: "currentcolor" }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M3 3H13V13H3V3Z"
        fill="currentColor"
      />
    </svg>
  );
};
