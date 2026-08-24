[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet(50001, 50002, 50003, 50004, 50005, 50018)]
  [int]$Port
)

$listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)

if ($listeners.Count -eq 0) {
  Write-Output "ARE port $Port is available."
  exit 0
}

foreach ($listener in $listeners) {
  $processName = "unknown process"

  try {
    $processName = (Get-Process -Id $listener.OwningProcess -ErrorAction Stop).ProcessName
  }
  catch {
    # The listener can exit between the network and process lookups.
  }

  Write-Error "ARE port $Port is occupied by $processName (PID $($listener.OwningProcess)) on $($listener.LocalAddress)."
}

exit 1
