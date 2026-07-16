namespace Nexor.Desktop.Presentation;
public static class BuildInfo
{
 public const string Version = "0.2.6";
#if TRIAL_EDITION
 public const bool IsTrial = true;
 public const string ProductName = "Nexor Trial";
 public const string EditionLabel = "Trial · avaliação local por 30 dias";
#else
 public const bool IsTrial = false;
 public const string ProductName = "Nexor";
 public const string EditionLabel = "Edição oficial";
#endif
}
