# Copyright 2017 Creu Blanca
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _order = "sequence"

    preinvoice_group_id = fields.Many2one(
        string="Pre-invoice Group", comodel_name="sale.preinvoice.group"
    )
    preinvoice_status = fields.Selection(
        related="preinvoice_group_id.state", readonly=True
    )
    is_validated = fields.Boolean(track_visibility=True)
    sequence = fields.Integer(string="Sequence", default="999999")

    @api.multi
    def validate_line(self):
        self.ensure_one()
        self.preinvoice_group_id.validate_line(self)

    @api.multi
    def invalidate_line(self):
        self.ensure_one()
        self.preinvoice_group_id.invalidate_line(self)

    @api.depends(
        "qty_invoiced",
        "qty_delivered",
        "product_uom_qty",
        "order_id.state",
        "invoice_group_method_id",
        "invoice_group_method_id.invoice_by_preinvoice",
        "invoice_group_method_id.no_invoice",
    )
    def _get_to_invoice_qty(self):
        for line in self:
            if line.invoice_group_method_id.no_invoice:
                line.qty_to_invoice = 0
            elif (
                line.invoice_group_method_id.invoice_by_preinvoice
                and not line.is_validated
            ):
                line.qty_to_invoice = 0
            else:
                super(SaleOrderLine, line)._get_to_invoice_qty()

    def _do_not_invoice(self):
        group = self.env.context.get("invoice_group_method_id", False)
        if group and group != self.invoice_group_method_id.id:
            return True
        return super()._do_not_invoice()

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res["invoice_group_method_id"] = self.invoice_group_method_id.id
        return res
