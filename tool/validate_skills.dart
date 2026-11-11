import 'package:skills_lint/skills_lint.dart';

const List<String> _defaultFlags = <String>['--print-warnings'];

/// Validates all skills configured in `skills_lint.yaml`.
///
/// Additional CLI flags such as `--fix`, `--dry-run`, or `--quiet` can be
/// forwarded directly via [args].
Future<void> main(List<String> args) async {
  final List<String> effectiveArgs = <String>[
    if (!args.contains('--help') && !args.contains('-h')) ..._defaultFlags,
    ...args,
  ];
  await runApp(effectiveArgs);
}
