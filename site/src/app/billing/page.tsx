import { redirect } from "next/navigation";

export default function BillingIndexRedirect() {
  redirect("/subscriptions");
}
